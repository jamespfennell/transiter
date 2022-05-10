package server

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	_ "github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/db/schema"
	"github.com/jamespfennell/transiter/internal/admin"
	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public"
	"github.com/jamespfennell/transiter/internal/scheduler"
	"github.com/jamespfennell/transiter/internal/update"
	"google.golang.org/grpc"
)

func Run(postgresHost string) error {
	log.Println("Starting Transiter v0.6alpha server")
	ctx := context.Background()
	ctx, cancelFunc := context.WithCancel(ctx)
	defer cancelFunc()

	config, err := pgxpool.ParseConfig(fmt.Sprintf("postgres://%s:%s@%s/%s?sslmode=disable",
		"transiter", // TODO user
		"transiter", // TODO password
		postgresHost,
		"transiter", // TODO database
	))
	if err != nil {
		return err
	}
	config.LazyConnect = true
	config.MaxConns = 50
	database, err := pgxpool.ConnectConfig(ctx, config)
	if err != nil {
		return fmt.Errorf("could not connect to DB: %w", err)
	}
	defer database.Close()

	if err := dbwrappers.Ping(ctx, database, 20, 500*time.Millisecond); err != nil {
		return fmt.Errorf("failed to connect to the database: %w", err)
	}

	log.Println("Database migrations: starting")
	if err := schema.Migrate(ctx, database); err != nil {
		log.Fatalf("Could not run the database migrations: %s\n", err)
	}
	log.Println("Database migrations: finished")

	var wg sync.WaitGroup
	scheduler, err := scheduler.New(ctx, clock.New(), database, func(database *pgxpool.Pool) db.Querier { return db.New(database) }, update.CreateAndRun)
	if err != nil {
		log.Fatalf("Failed to intialize the scheduler: %s\n", err)
	}

	publicService := public.New(database)
	adminService := admin.New(database, scheduler)

	wg.Add(1)
	go func() {
		defer cancelFunc()
		defer wg.Done()
		mux := runtime.NewServeMux(
			apihelpers.MarshalerOptions(),
			apihelpers.IncomingHeaderMatcher(),
			apihelpers.ErrorHandler(),
		)
		api.RegisterPublicHandlerServer(ctx, mux, publicService)
		log.Println("Public service HTTP API listening on localhost:8080")
		err := http.ListenAndServe("localhost:8080", mux)
		fmt.Printf("Closing :8080: %s\n", err)
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
		mux := runtime.NewServeMux(
			apihelpers.MarshalerOptions(),
			apihelpers.IncomingHeaderMatcher(),
			apihelpers.ErrorHandler(),
		)
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
	scheduler.Wait()
	return nil
}
