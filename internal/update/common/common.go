// Package common contains types used by all update code.
package common

import (
	"crypto/md5"
	"encoding/json"
	"fmt"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

type UpdateContext struct {
	Querier    db.Querier
	SystemPk   int64
	FeedPk     int64
	UpdatePk   int64
	FeedConfig *api.FeedConfig
}

func HashBytes(b []byte) string {
	return fmt.Sprintf("%x", md5.Sum(b))
}

func HashValue(a any) (string, error) {
	b, err := json.Marshal(a)
	if err != nil {
		return "", err
	}
	return HashBytes(b), nil
}
