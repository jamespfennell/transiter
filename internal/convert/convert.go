// Package convert contains type converters.
package convert

import (
	"database/sql"
	"time"

	"github.com/jamespfennell/gtfs"
)

func SQLNullTime(t sql.NullTime) *int64 {
	if !t.Valid {
		return nil
	}
	r := t.Time.Unix()
	return &r
}

func SQLNullString(t sql.NullString) *string {
	if !t.Valid {
		return nil
	}
	return &t.String
}

func SQLNullFloat64(t sql.NullFloat64) *float64 {
	if !t.Valid {
		return nil
	}
	return &t.Float64
}

func SQLNullInt32(t sql.NullInt32) *int32 {
	if !t.Valid {
		return nil
	}
	return &t.Int32
}

func NullInt32(t *int32) sql.NullInt32 {
	if t == nil {
		return sql.NullInt32{}
	}
	return sql.NullInt32{Valid: true, Int32: *t}
}

func NullInt64(t *int64) sql.NullInt64 {
	if t == nil {
		return sql.NullInt64{}
	}
	return sql.NullInt64{Valid: true, Int64: *t}
}

func NullString(t *string) sql.NullString {
	if t == nil {
		return sql.NullString{}
	}
	return sql.NullString{Valid: true, String: *t}
}

func DirectionID(d gtfs.DirectionID) sql.NullBool {
	switch d {
	case gtfs.DirectionIDFalse:
		return sql.NullBool{
			Valid: true,
			Bool:  false,
		}
	case gtfs.DirectionIDTrue:
		return sql.NullBool{
			Valid: true,
			Bool:  true,
		}
	default:
		return sql.NullBool{
			Valid: false,
		}
	}
}

func NullTime(t *time.Time) sql.NullTime {
	if t == nil {
		return sql.NullTime{}
	}
	return sql.NullTime{
		Valid: true,
		Time:  *t,
	}
}

func NullDuration(d *time.Duration) sql.NullInt32 {
	if d == nil {
		return sql.NullInt32{}
	}
	return sql.NullInt32{
		Valid: true,
		Int32: int32(d.Milliseconds() / 1000),
	}
}
