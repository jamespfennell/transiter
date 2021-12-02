package main

import (
	"context"
	"database/sql"
	"log"
	"net"
	"net/http"
	"sync"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	_ "github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/service"
	"google.golang.org/grpc"
)

func main() {
	log.Println("Transiter v0.6alpha")
	db, err := sql.Open("postgres", "user=transiter dbname=transiter password=transiter sslmode=disable")
	if err != nil {
		log.Fatalf("Could not connect to DB: %s\n", err)
	}
	transiterService := service.NewTransiterService(db)

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

	wg.Wait()
}
