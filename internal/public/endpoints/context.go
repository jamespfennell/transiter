package endpoints

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/public/href"
)

type Context struct {
	Querier db.Querier
	Href    href.Generator
}

func getSystem(ctx context.Context, querier db.Querier, id string) (db.System, error) {
	system, err := querier.GetSystem(ctx, id)
	return system, noRowsToNotFound(err, fmt.Sprintf("system %q", id))
}

func noRowsToNotFound(err error, notFoundText string) error {
	if err == pgx.ErrNoRows {
		err = errors.NewNotFoundError(notFoundText + " does not exist")
	}
	return err
}
