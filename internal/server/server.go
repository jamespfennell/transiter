package server

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	_ "github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/db/schema"
	"github.com/jamespfennell/transiter/internal/admin"
	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public"
	"github.com/jamespfennell/transiter/internal/scheduler"
	"github.com/jamespfennell/transiter/internal/update"
	"google.golang.org/grpc"
)

func Run(postgresHost string) error {
	log.Println("Starting Transiter v0.6alpha server")
	database, err := sql.Open("postgres", fmt.Sprintf("postgres://%s:%s@%s/%s?sslmode=disable",
		"transiter", // user
		"transiter", // password
		postgresHost,
		"transiter", // database
	))
	if err != nil {
		log.Fatalf("Could not connect to DB: %s\n", err)
	}

	if err := pingDb(database); err != nil {
		log.Fatalf("Failed to connect to the database; exiting: %s\n", err)
	}

	log.Println("Database migrations: starting")
	if err := schema.Migrate(database); err != nil {
		log.Fatalf("Could not run the database migrations: %s\n", err)
	}
	log.Println("Database migrations: finished")

	ctx := context.Background()
	ctx, cancelFunc := context.WithCancel(ctx)
	defer cancelFunc()

	var wg sync.WaitGroup
	scheduler, err := scheduler.New(ctx, clock.New(), database, func(database *sql.DB) db.Querier { return db.New(database) }, update.Run)
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
		log.Println("Transiter service HTTP API listening on localhost:8080")
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
		log.Println("Transiter service gRPC API listening on localhost:8081")
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

func pingDb(db *sql.DB) error {
	var err error
	nRetries := 20
	for i := 0; i < nRetries; i++ {
		err = db.Ping()
		if err == nil {
			log.Printf("Database ping successful")
			break
		}
		log.Printf("Failed to ping the database: %s\n", err)
		if i != nRetries-1 {
			log.Printf("Will try to ping agaion in 500 milliseconds")
			time.Sleep(500 * time.Millisecond)
		}
	}
	return err
}
