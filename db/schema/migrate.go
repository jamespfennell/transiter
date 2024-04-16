// Package schema contains the migrations runner.
package schema

import (
	"context"
	"embed"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jackc/tern/v2/migrate"
)

//go:embed *.sql
var migrations embed.FS

// Migrate applies all migrations to the databse.
func Migrate(ctx context.Context, pool *pgxpool.Pool) error {
	conn, err := pool.Acquire(ctx)
	defer conn.Release()
	if err != nil {
		return err
	}
	m, err := migrate.NewMigratorEx(ctx, conn.Conn(), "public.schema_version", &migrate.MigratorOptions{})
	if err != nil {
		return err
	}
	if err := m.LoadMigrations(migrations); err != nil {
		return err
	}
	return m.Migrate(ctx)
}
