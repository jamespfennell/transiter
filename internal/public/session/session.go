package session

import (
	"context"
	"database/sql"
	"log"

	"github.com/jamespfennell/transiter/internal/gen/db"
)

type Session struct {
	tx      *sql.Tx
	Querier db.Querier
	Hrefs   HrefGenerator
}

func NewSession(database *sql.DB, ctx context.Context) Session {
	tx, err := database.BeginTx(ctx, nil)
	if err != nil {
		log.Fatal("Failed to start a database transaction", err)
	}
	return Session{
		tx:      tx,
		Querier: db.New(tx),
		Hrefs:   NewHrefGenerator(ctx),
	}
}

func (s *Session) Cleanup() {
	s.tx.Rollback()
}

func (s *Session) Finish() error {
	// TODO: nicer error?
	return s.tx.Commit()
}
