// Package server implements the Transiter server process.
package server

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"net/http/pprof"
	"os"
	"sync"
	"time"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamespfennell/transiter/db/schema"
	"github.com/jamespfennell/transiter/internal/admin"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/monitoring"
	"github.com/jamespfennell/transiter/internal/public"
	"github.com/jamespfennell/transiter/internal/public/endpoints"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/public/reference"
	"github.com/jamespfennell/transiter/internal/scheduler"
	"golang.org/x/exp/slog"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/encoding/protojson"
)

type RunArgs struct {
	PublicHTTPAddr        string
	PublicGrpcAddr        string
	AdminHTTPAddr         string
	AdminGrpcAddr         string
	PostgresConnStr       string
	MaxConnections        int32
	DisableScheduler      bool
	DisablePublicMetrics  bool
	EnablePprof           bool
	ReadOnly              bool
	MaxStopsPerRequest    int32
	MaxVehiclesPerRequest int32
	LogLevel              slog.Level
}

func Run(ctx context.Context, args RunArgs) error {
	var levelVar slog.LevelVar
	levelVar.Set(args.LogLevel)

	handerOptions := slog.HandlerOptions{
		Level: &levelVar,
	}.NewTextHandler(os.Stdout)
	logger := slog.New(handerOptions)
	logger.InfoCtx(ctx, "starting Transiter server")
	ctx, cancelFunc := context.WithCancel(ctx)
	defer cancelFunc()

	config, err := pgxpool.ParseConfig(args.PostgresConnStr)
	if err != nil {
		return err
	}
	// TODO config.LazyConnect = true
	config.MaxConns = args.MaxConnections
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return fmt.Errorf("could not connect to database: %w", err)
	}
	defer func() {
		logger.InfoCtx(ctx, "closing database pool")
		pool.Close()
	}()

	if err := dbwrappers.Ping(ctx, logger, pool, 20, 500*time.Millisecond); err != nil {
		return fmt.Errorf("failed to connect to the database: %w", err)
	}

	if !args.ReadOnly {
		logger.InfoCtx(ctx, "starting database migrations")
		if err := schema.Migrate(ctx, pool); err != nil {
			return fmt.Errorf("failed to run Transiter database migrations: %w", err)
		}
		logger.InfoCtx(ctx, "finished database migrations")
	} else {
		logger.InfoCtx(ctx, "skipping database migrations because Transiter is in read-only mode")
	}

	var wg sync.WaitGroup

	var realScheduler *scheduler.DefaultScheduler
	var s scheduler.Scheduler

	if args.DisableScheduler || args.ReadOnly {
		s = scheduler.NoOpScheduler(logger)
	} else {
		realScheduler = scheduler.NewDefaultScheduler()
		s = realScheduler
	}

	monitoring := monitoring.NewPrometheusMonitoring("transiter")
	publicService := public.New(pool, logger, monitoring, &endpoints.EndpointOptions{
		MaxStopsPerRequest: args.MaxStopsPerRequest,
	})
	adminService := admin.New(pool, s, logger, &levelVar, monitoring)

	if realScheduler != nil {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			realScheduler.Run(ctx, publicService, adminService, logger)
			logger.InfoCtx(ctx, "scheduler stopped")
		}()
		if err := realScheduler.Reset(ctx); err != nil {
			return fmt.Errorf("failed to initialize the scheduler: %w", err)
		}
		logger.InfoCtx(ctx, "scheduler running")
	}

	var shutdownFuncs []func(context.Context) error

	if args.PublicHTTPAddr != "-" {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			mux := newServeMux(logger)
			api.RegisterPublicHandlerServer(ctx, mux, publicService)
			h := http.NewServeMux()
			h.Handle("/", mux)
			if !args.DisablePublicMetrics {
				h.Handle("/metrics", monitoring.Handler())
			}
			server := &http.Server{Addr: args.PublicHTTPAddr, Handler: h}
			shutdownFuncs = append(shutdownFuncs, server.Shutdown)
			logger.InfoCtx(ctx, fmt.Sprintf("public HTTP API listening on %s", args.PublicHTTPAddr))
			server.ListenAndServe()
			logger.InfoCtx(ctx, "public HTTP API stopped")
		}()
	}

	if args.PublicGrpcAddr != "-" {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			grpcServer := grpc.NewServer()
			shutdownFuncs = append(shutdownFuncs, func(ctx context.Context) error {
				grpcServer.GracefulStop()
				return nil
			})
			api.RegisterPublicServer(grpcServer, publicService)
			lis, err := net.Listen("tcp", args.PublicGrpcAddr)
			if err != nil {
				logger.ErrorCtx(ctx, fmt.Sprintf("failed to launch public gRPC API: %s", err))
				return
			}
			logger.InfoCtx(ctx, fmt.Sprintf("public gRPC API listening on %s", args.PublicGrpcAddr))
			_ = grpcServer.Serve(lis)
			logger.InfoCtx(ctx, "public gRPC API stopped")
		}()
	}

	if args.AdminHTTPAddr != "-" && !args.ReadOnly {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			mux := newServeMux(logger)
			api.RegisterPublicHandlerServer(ctx, mux, publicService)
			api.RegisterAdminHandlerServer(ctx, mux, adminService)
			h := http.NewServeMux()
			h.Handle("/", mux)
			h.Handle("/metrics", monitoring.Handler())
			if args.EnablePprof {
				registerPprofHandlers(h)
			}
			server := &http.Server{Addr: args.AdminHTTPAddr, Handler: h}
			shutdownFuncs = append(shutdownFuncs, server.Shutdown)
			logger.InfoCtx(ctx, fmt.Sprintf("admin HTTP API listening on %s", args.AdminHTTPAddr))
			server.ListenAndServe()
			logger.InfoCtx(ctx, "admin HTTP API stopped")
		}()
	}

	if args.AdminGrpcAddr != "-" && !args.ReadOnly {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			grpcServer := grpc.NewServer()
			shutdownFuncs = append(shutdownFuncs, func(ctx context.Context) error {
				grpcServer.GracefulStop()
				return nil
			})
			api.RegisterPublicServer(grpcServer, publicService)
			api.RegisterAdminServer(grpcServer, adminService)
			lis, err := net.Listen("tcp", args.AdminGrpcAddr)
			if err != nil {
				logger.ErrorCtx(ctx, fmt.Sprintf("failed to launch admin gRPC API: %s", err))
				return
			}
			logger.InfoCtx(ctx, fmt.Sprintf("admin gRPC API listening on %s", args.AdminGrpcAddr))
			_ = grpcServer.Serve(lis)
			logger.InfoCtx(ctx, "admin gRPC API stopped")
		}()
	}

	<-ctx.Done()
	logger.InfoCtx(ctx, "recieved cancellation signal; starting server shutdown")
	for _, f := range shutdownFuncs {
		f(context.Background())
	}
	wg.Wait()
	logger.InfoCtx(ctx, "server shutdown complete")
	return ctx.Err()
}

func newServeMux(logger *slog.Logger) *runtime.ServeMux {
	return runtime.NewServeMux(
		// Option to marshal the JSON in a nice way
		runtime.WithMarshalerOption("*", &runtime.JSONPb{
			MarshalOptions: protojson.MarshalOptions{
				Indent:          "  ",
				Multiline:       true,
				EmitUnpopulated: true,
			}}),
		// Option to match the X-Transiter host header
		runtime.WithIncomingHeaderMatcher(
			func(key string) (string, bool) {
				switch key {
				case reference.XTransiterHost:
					return key, true
				default:
					return runtime.DefaultHeaderMatcher(key)
				}
			}),
		// Option to map internal errors to nice HTTP error
		errors.ServeMuxOption(logger),
	)
}

func registerPprofHandlers(h *http.ServeMux) {
	h.HandleFunc("/debug/pprof/", pprof.Index)
	h.HandleFunc("/debug/pprof/cmdline", pprof.Cmdline)
	h.HandleFunc("/debug/pprof/profile", pprof.Profile)
	h.HandleFunc("/debug/pprof/symbol", pprof.Symbol)
	h.HandleFunc("/debug/pprof/trace", pprof.Trace)
}
