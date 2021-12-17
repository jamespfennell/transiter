package update

import (
	"context"
	"database/sql"
	"log"

	"github.com/jamespfennell/transiter/internal/gen/db"
)

func Run(ctx context.Context, database *sql.DB, systemId, feedId string) error {
	tx, err := database.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	err = RunWithQuerier(ctx, db.New(tx), systemId, feedId)
	if err != nil {
		return err
	}
	tx.Commit()
	return nil
}

func RunWithQuerier(ctx context.Context, querier db.Querier, systemId, feedId string) error {
	log.Printf("Starting update for %s/%s\n", systemId, feedId)
	return nil
}
