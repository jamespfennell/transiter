package graphql

import (
	"net/http"

	"github.com/99designs/gqlgen/graphql/handler"
	"github.com/jackc/pgx/v5/pgxpool"
)

func NewHandler(pool *pgxpool.Pool) http.Handler {
	srv := handler.NewDefaultServer(NewExecutableSchema(Config{
		Resolvers: &Resolver{Pool: pool},
	}))
	return DataloaderMiddleware(pool)(srv)
}
