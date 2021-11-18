package main

import (
	"context"
	"database/sql"
	"log"
	"net/http"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/jamespfennell/transiter/internal/gen/api"
	tdb "github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/server"
	_ "github.com/lib/pq"
	"google.golang.org/protobuf/encoding/protojson"
)

func CustomMatcher(key string) (string, bool) {
	switch key {
	case "X-Transiter-Base-Url":
		return key, true
	default:
		return runtime.DefaultHeaderMatcher(key)
	}
}

func main() {
	log.Println("Transiter v0.6alpha")
	ctx := context.Background()
	db, err := sql.Open("postgres", "user=transiter dbname=transiter password=transiter sslmode=disable")
	if err != nil {
		log.Fatalf("Could not connect to DB: %s\n", err)
	}
	queries := tdb.New(db)
	//port := 8080
	//lis, err := net.Listen("tcp", fmt.Sprintf("localhost:%d", port))
	//if err != nil {
	//	log.Fatalf("failed to listen: %v", err)
	//}
	mux := runtime.NewServeMux(
		runtime.WithMarshalerOption("*", &runtime.JSONPb{
			MarshalOptions: protojson.MarshalOptions{
				Indent:          "  ",
				Multiline:       true,
				EmitUnpopulated: true,
			}}),
		runtime.WithIncomingHeaderMatcher(CustomMatcher),
	)
	api.RegisterTransiterHandlerServer(ctx, mux, server.NewTransiterServer(queries))
	// Start HTTP server (and proxy calls to gRPC server endpoint)
	_ = http.ListenAndServe(":8081", mux)

	//var opts []grpc.ServerOption
	//grpcServer := grpc.NewServer(opts...)
	//api.RegisterTransiterServer(grpcServer, &transiterServer{querier: queries})
	//grpcServer.Serve(lis)
}
