package graphql

import (
	"net/http"

	"github.com/99designs/gqlgen/graphql/handler"
	"github.com/99designs/gqlgen/graphql/playground"
	"github.com/jackc/pgx/v5/pgxpool"
)

func NewHandler(pool *pgxpool.Pool) http.Handler {
	srv := DataloaderMiddleware(pool)(handler.NewDefaultServer(NewExecutableSchema(Config{
		Resolvers: &Resolver{Pool: pool},
	})))
	pg := playground.Handler("Transiter", "/graphql")
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet {
			pg.ServeHTTP(w, r)
			return
		}
		srv.ServeHTTP(w, r)
	})
}
