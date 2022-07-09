// Package convert contains type converters.
package convert

import (
	"database/sql"
	"encoding/json"
	"time"

	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/gen/api"
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

func AlertText(s string) []*api.Alert_Text {
	var in []gtfs.AlertText
	json.Unmarshal([]byte(s), &in)
	var out []*api.Alert_Text
	for _, text := range in {
		out = append(out, &api.Alert_Text{
			Text:     text.Text,
			Language: text.Language,
		})
	}
	return out
}

func AlertCause(cause string) api.Alert_Cause {
	return api.Alert_Cause(api.Alert_Cause_value[cause])
}

func AlertEffect(effect string) api.Alert_Effect {
	return api.Alert_Effect(api.Alert_Effect_value[effect])
}

func AlertPreview(id, cause, effect string) *api.Alert_Preview {
	return &api.Alert_Preview{
		Id:     id,
		Cause:  AlertCause(cause),
		Effect: AlertEffect(effect),
	}
}

func TransferType(t string) api.Transfer_Type {
	return api.Transfer_Type(api.Transfer_Type_value[t])
}