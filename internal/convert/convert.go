package convert

import (
	"database/sql"
)

func SqlNullTime(t sql.NullTime) *int64 {
	if !t.Valid {
		return nil
	}
	r := t.Time.Unix()
	return &r
}

func SqlNullString(t sql.NullString) *string {
	if !t.Valid {
		return nil
	}
	return &t.String
}

func SqlNullFloat64(t sql.NullFloat64) *float64 {
	if !t.Valid {
		return nil
	}
	return &t.Float64
}

func SqlNullInt32(t sql.NullInt32) *int32 {
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
