package session

import (
	"context"
	"log"

	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

type Session struct {
	ctx     context.Context
	tx      pgx.Tx
	Querier db.Querier
	Hrefs   HrefGenerator
}

func NewSession(ctx context.Context, pool *pgxpool.Pool) Session {
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{})
	if err != nil {
		log.Fatal("Failed to start a database transaction", err)
	}
	return Session{
		ctx:     ctx,
		tx:      tx,
		Querier: db.New(tx),
		Hrefs:   NewHrefGenerator(ctx),
	}
}

func (s *Session) Cleanup() {
	// TODO: return the error here
	s.tx.Rollback(s.ctx)
}

func (s *Session) Finish() error {
	return s.tx.Commit(s.ctx)
}
