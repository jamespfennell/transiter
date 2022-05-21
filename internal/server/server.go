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
	"github.com/jamespfennell/transiter/internal/public"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/public/href"
	"github.com/jamespfennell/transiter/internal/scheduler"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/encoding/protojson"
)

type RunArgs struct {
	PublicHTTPAddr   string
	PostgresAddress  string
	PostgresUser     string
	PostgresPassword string
	PostgresDatabase string
	MaxConnections   int32
}

func Run(args RunArgs) error {
	log.Println("Starting Transiter v0.6alpha server")
	ctx := context.Background()
	ctx, cancelFunc := context.WithCancel(ctx)
	defer cancelFunc()

	// TODO: just provide a postgres connection string? I think this would be simpler
	config, err := pgxpool.ParseConfig(fmt.Sprintf("postgres://%s:%s@%s/%s?sslmode=disable",
		args.PostgresUser,
		args.PostgresPassword,
		args.PostgresAddress,
		args.PostgresDatabase,
	))
	if err != nil {
		return err
	}
	config.LazyConnect = true
	config.MaxConns = args.MaxConnections
	pool, err := pgxpool.ConnectConfig(ctx, config)
	if err != nil {
		return fmt.Errorf("could not connect to DB: %w", err)
	}
	defer pool.Close()

	if err := dbwrappers.Ping(ctx, pool, 20, 500*time.Millisecond); err != nil {
		return fmt.Errorf("failed to connect to the database: %w", err)
	}

	log.Println("Database migrations: starting")
	if err := schema.Migrate(ctx, pool); err != nil {
		log.Fatalf("Could not run the database migrations: %s\n", err)
	}
	log.Println("Database migrations: finished")

	var wg sync.WaitGroup
	scheduler := scheduler.New()

	wg.Add(1)
	go func() {
		scheduler.Run(ctx, pool)
		wg.Done()
	}()
	if err := scheduler.ResetAll(ctx); err != nil {
		return fmt.Errorf("failed to intialize the scheduler: %w", err)
	}

	publicService := public.New(pool)
	adminService := admin.New(pool, scheduler)

	wg.Add(1)
	go func() {
		defer cancelFunc()
		defer wg.Done()
		mux := newServeMux()
		api.RegisterPublicHandlerServer(ctx, mux, publicService)
		log.Printf("Public HTTP server listening on %s\n", args.PublicHTTPAddr)
		err := http.ListenAndServe(args.PublicHTTPAddr, mux)
		fmt.Printf("Closing public service HTTP: %s\n", err)
	}()

	wg.Add(1)
	go func() {
		defer cancelFunc()
		defer wg.Done()
		grpcServer := grpc.NewServer()
		api.RegisterPublicServer(grpcServer, publicService)
		lis, err := net.Listen("tcp", "localhost:8081")
		if err != nil {
			return
		}
		log.Println("Public service gRPC API listening on localhost:8081")
		_ = grpcServer.Serve(lis)
	}()

	wg.Add(1)
	go func() {
		defer cancelFunc()
		defer wg.Done()
		mux := newServeMux()
		api.RegisterPublicHandlerServer(ctx, mux, publicService)
		api.RegisterTransiterAdminHandlerServer(ctx, mux, adminService)
		log.Println("Admin service HTTP API listening on localhost:8082")
		_ = http.ListenAndServe("0.0.0.0:8082", mux)
	}()

	wg.Add(1)
	go func() {
		defer cancelFunc()
		defer wg.Done()
		grpcServer := grpc.NewServer()
		api.RegisterPublicServer(grpcServer, publicService)
		api.RegisterTransiterAdminServer(grpcServer, adminService)
		lis, err := net.Listen("tcp", "localhost:8083")
		if err != nil {
			return
		}
		log.Println("Admin service gRPC API listening on localhost:8083")
		_ = grpcServer.Serve(lis)
	}()

	wg.Wait()
	return nil
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
				case href.XTransiterHost:
					return key, true
				default:
					return runtime.DefaultHeaderMatcher(key)
				}
			}),
		// Option to map internal errors to nice HTTP error
		errors.ServeMuxOption(),
	)
}
