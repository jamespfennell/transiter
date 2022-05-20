package endpoints

import (
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/href"
)

type Context struct {
	Querier db.Querier
	Href    href.Generator
}
