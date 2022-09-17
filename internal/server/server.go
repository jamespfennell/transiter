// Package server implements the Transiter server process.
package server

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/db/schema"
	"github.com/jamespfennell/transiter/internal/admin"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/monitoring"
	"github.com/jamespfennell/transiter/internal/public"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/public/reference"
	"github.com/jamespfennell/transiter/internal/scheduler"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/encoding/protojson"
)

type RunArgs struct {
	PublicHTTPAddr   string
	PublicGrpcAddr   string
	AdminHTTPAddr    string
	AdminGrpcAddr    string
	PostgresConnStr  string
	MaxConnections   int32
	DisableScheduler bool
	NoPublicMetrics  bool
	ReadOnly         bool
}

func Run(ctx context.Context, args RunArgs) error {
	log.Println("Starting Transiter v0.6alpha server")
	ctx, cancelFunc := context.WithCancel(ctx)
	defer cancelFunc()

	config, err := pgxpool.ParseConfig(args.PostgresConnStr)
	if err != nil {
		return err
	}
	config.LazyConnect = true
	config.MaxConns = args.MaxConnections
	pool, err := pgxpool.ConnectConfig(ctx, config)
	if err != nil {
		return fmt.Errorf("could not connect to database: %w", err)
	}
	defer func() {
		log.Printf("Database pool: closing")
		pool.Close()
		log.Printf("Database pool: closed")
	}()

	if err := dbwrappers.Ping(ctx, pool, 20, 500*time.Millisecond); err != nil {
		return fmt.Errorf("failed to connect to the database: %w", err)
	}

	if !args.ReadOnly {
		log.Println("Database migrations: starting")
		if err := schema.Migrate(ctx, pool); err != nil {
			log.Fatalf("Could not run the database migrations: %s\n", err)
		}
		log.Println("Database migrations: finished")
	} else {
		log.Println("Database migrations: skipping because in read only mode")
	}

	var wg sync.WaitGroup

	var realScheduler *scheduler.DefaultScheduler
	var s scheduler.Scheduler

	if args.DisableScheduler || args.ReadOnly {
		s = scheduler.NoOpScheduler()
	} else {
		realScheduler = scheduler.NewDefaultScheduler()
		s = realScheduler
	}

	publicService := public.New(pool)
	adminService := admin.New(pool, s)

	if realScheduler != nil {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			realScheduler.Run(ctx, publicService, adminService)
			log.Printf("Scheduler stopped")
		}()
		if err := realScheduler.Reset(ctx); err != nil {
			return fmt.Errorf("failed to intialize the scheduler: %w", err)
		}
		log.Println("Scheduler running")
	}

	if args.PublicHTTPAddr != "-" {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			mux := newServeMux()
			api.RegisterPublicHandlerServer(ctx, mux, publicService)
			h := http.NewServeMux()
			h.Handle("/", mux)
			if !args.NoPublicMetrics {
				h.Handle("/metrics", monitoring.Handler())
			}
			log.Printf("Public HTTP API listening on %s\n", args.PublicHTTPAddr)
			_ = http.ListenAndServe(args.PublicHTTPAddr, h)
			log.Printf("Public HTTP API stopped")
		}()
	}

	if args.PublicGrpcAddr != "-" {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			grpcServer := grpc.NewServer()
			api.RegisterPublicServer(grpcServer, publicService)
			lis, err := net.Listen("tcp", args.PublicGrpcAddr)
			if err != nil {
				log.Printf("Failed to launch public gRPC API: %s", err)
				return
			}
			log.Printf("Public gRPC API listening on %s\n", args.PublicGrpcAddr)
			_ = grpcServer.Serve(lis)
			log.Printf("Public gRPC API stopped")
		}()
	}

	if args.AdminHTTPAddr != "-" && !args.ReadOnly {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			mux := newServeMux()
			api.RegisterPublicHandlerServer(ctx, mux, publicService)
			api.RegisterAdminHandlerServer(ctx, mux, adminService)
			log.Printf("Admin HTTP API listening on %s", args.AdminHTTPAddr)
			http.ListenAndServe(args.AdminHTTPAddr, mux)
			log.Printf("Admin HTTP API stopped")
		}()
	}

	if args.AdminGrpcAddr != "-" && !args.ReadOnly {
		wg.Add(1)
		go func() {
			defer cancelFunc()
			defer wg.Done()
			grpcServer := grpc.NewServer()
			api.RegisterPublicServer(grpcServer, publicService)
			api.RegisterAdminServer(grpcServer, adminService)
			lis, err := net.Listen("tcp", args.AdminGrpcAddr)
			if err != nil {
				log.Printf("Failed to launch admin gRPC API: %s", err)
				return
			}
			log.Printf("Admin gRPC API listening on %s\n", args.AdminGrpcAddr)
			_ = grpcServer.Serve(lis)
			log.Printf("Admin gRPC API stopped")
		}()
	}

	wg.Wait()
	log.Printf("Shutting down server")
	return ctx.Err()
}

func newServeMux() *runtime.ServeMux {
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
		errors.ServeMuxOption(),
	)
}
