package schema

import (
	"database/sql"
	"embed"

	"github.com/pressly/goose/v3"
)

//go:embed *.sql
var migrations embed.FS

// Applies all migratons to the databse.
func Migrate(database *sql.DB) error {
	goose.SetBaseFS(migrations)
	return goose.Up(database, ".")
}
