package main

import (
	"context"
	"database/sql"
	"flag"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	_ "github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/db/schema"
	"github.com/jamespfennell/transiter/internal/admin"
	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/service"
	"google.golang.org/grpc"
)

var flagPostgresHost = flag.String("postgres-host", "localhost:5432", "the help message for flag n")

func main() {
	flag.Parse()
	log.Println("Transiter v0.6alpha")
	db, err := sql.Open("postgres", fmt.Sprintf("postgres://%s:%s@%s/%s?sslmode=disable",
		"transiter",       // user
		"transiter",       // password
		*flagPostgresHost, // Postgres host
		"transiter",       // database
	))
	if err != nil {
		log.Fatalf("Could not connect to DB: %s\n", err)
	}

	if err := pingDb(db); err != nil {
		log.Fatalf("Failed to connect to the database; exiting: %s\n", err)
	}

	log.Println("Database migrations: starting")
	if err := schema.Migrate(db); err != nil {
		log.Fatalf("Could not run the database migrations: %s\n", err)
	}
	log.Println("Database migrations: finished")

	transiterService := service.NewTransiterService(db)
	adminService := admin.New(db)

	ctx := context.Background()
	ctx, cancelFunc := context.WithCancel(ctx)
	defer cancelFunc()

	var wg sync.WaitGroup

	wg.Add(1)
	go func() {
		defer cancelFunc()
		defer wg.Done()
		mux := runtime.NewServeMux(
			apihelpers.MarshalerOptions(),
			apihelpers.IncomingHeaderMatcher(),
			apihelpers.ErrorHandler(),
		)
		api.RegisterTransiterHandlerServer(ctx, mux, transiterService)
		log.Println("Transiter service HTTP API listening on localhost:8080")
		_ = http.ListenAndServe("localhost:8080", mux)
	}()

	wg.Add(1)
	go func() {
		defer cancelFunc()
		defer wg.Done()
		grpcServer := grpc.NewServer()
		api.RegisterTransiterServer(grpcServer, transiterService)
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
		api.RegisterTransiterHandlerServer(ctx, mux, transiterService)
		api.RegisterTransiterAdminHandlerServer(ctx, mux, adminService)
		log.Println("Admin service HTTP API listening on localhost:8082")
		_ = http.ListenAndServe("0.0.0.0:8082", mux)
	}()

	wg.Add(1)
	go func() {
		defer cancelFunc()
		defer wg.Done()
		grpcServer := grpc.NewServer()
		api.RegisterTransiterServer(grpcServer, transiterService)
		api.RegisterTransiterAdminServer(grpcServer, adminService)
		lis, err := net.Listen("tcp", "localhost:8083")
		if err != nil {
			return
		}
		log.Println("Admin service gRPC API listening on localhost:8083")
		_ = grpcServer.Serve(lis)
	}()

	wg.Wait()
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
