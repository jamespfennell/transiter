// Package schema contains the migrations runner.
package schema

import (
	"context"
	"embed"
	"io/fs"
	"os"

	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jackc/tern/migrate"
)

//go:embed *.sql
var migrations embed.FS

// Migrate applies all migrations to the databse.
func Migrate(ctx context.Context, pool *pgxpool.Pool) error {
	conn, err := pool.Acquire(ctx)
	if err != nil {
		return err
	}
	m, err := migrate.NewMigratorEx(context.Background(), conn.Conn(), "public.schema_version", &migrate.MigratorOptions{
		MigratorFS: NewFS(migrations),
	})
	if err != nil {
		return err
	}
	if err := m.LoadMigrations("."); err != nil {
		return err
	}
	return m.Migrate(ctx)
}

// NewFS returns a MigratorFS that uses as fs.FS filesystem.
func NewFS(fsys fs.FS) migrate.MigratorFS {
	return iofsMigratorFS{fsys: fsys}
}

type iofsMigratorFS struct{ fsys fs.FS }

// ReadDir implements the MigratorFS interface.
func (m iofsMigratorFS) ReadDir(dirname string) ([]fs.FileInfo, error) {
	d, err := fs.ReadDir(m.fsys, dirname)
	if err != nil {
		return nil, err
	}
	var fis []os.FileInfo
	for _, v := range d {
		fi, err := v.Info()
		if err != nil {
			return nil, err
		}
		fis = append(fis, fi)
	}
	return fis, nil
}

// ReadFile implements the MigratorFS interface.
func (m iofsMigratorFS) ReadFile(filename string) ([]byte, error) {
	return fs.ReadFile(m.fsys, filename)
}

// Glob implements the MigratorFS interface.
func (m iofsMigratorFS) Glob(pattern string) (matches []string, err error) {
	return fs.Glob(m.fsys, pattern)
}
