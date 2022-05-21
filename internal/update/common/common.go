// Package common contains types used by all update code.
package common

import "github.com/jamespfennell/transiter/internal/gen/db"

type UpdateContext struct {
	Querier  db.Querier
	SystemPk int64
	FeedPk   int64
	UpdatePk int64
}
