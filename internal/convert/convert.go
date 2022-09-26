// Package convert contains type converters.
package convert

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/gtfs/extensions"
	"github.com/jamespfennell/gtfs/extensions/nyctalerts"
	"github.com/jamespfennell/gtfs/extensions/nycttrips"
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

func SQLNullInt64(t sql.NullInt64) *int64 {
	if !t.Valid {
		return nil
	}
	return &t.Int64
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

func NullFloat64(t *float64) sql.NullFloat64 {
	if t == nil {
		return sql.NullFloat64{}
	}
	return sql.NullFloat64{Valid: true, Float64: *t}
}

func NullString(t *string) sql.NullString {
	if t == nil {
		return sql.NullString{}
	}
	return sql.NullString{Valid: true, String: *t}
}

func NullBool(t *bool) sql.NullBool {
	if t == nil {
		return sql.NullBool{}
	}
	return sql.NullBool{Valid: true, Bool: *t}
}

func SQLNullBool(t sql.NullBool) *bool {
	if !t.Valid {
		return nil
	}
	return &t.Bool
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

func TransferType(t string) api.Transfer_Type {
	return api.Transfer_Type(api.Transfer_Type_value[t])
}

func StopType(t string) api.Stop_Type {
	return api.Stop_Type(api.Stop_Type_value[t])
}

func FeedUpdateResult(result sql.NullString) *api.FeedUpdate_Result {
	if !result.Valid {
		return nil
	}
	if i, ok := api.FeedUpdate_Result_value[result.String]; ok {
		return api.FeedUpdate_Result(i).Enum()
	}
	log.Printf("Unknown feed update result %s\n", result.String)
	return api.FeedUpdate_INTERNAL_ERROR.Enum()
}

func ContinuousPolicy(p string) api.Route_ContinuousPolicy {
	if i, ok := api.Route_ContinuousPolicy_value[p]; ok {
		return api.Route_ContinuousPolicy(i)
	}
	return api.Route_NOT_ALLOWED
}

func RouteType(t string) api.Route_Type {
	if i, ok := api.Route_Type_value[t]; ok {
		return api.Route_Type(i)
	}
	return api.Route_UNKNOWN
}

func GtfsRealtimeExtension(in *api.GtfsRealtimeOptions) (extensions.Extension, error) {
	if in == nil {
		in = &api.GtfsRealtimeOptions{}
	}
	switch in.Extension {
	case api.GtfsRealtimeOptions_NO_EXTENSION:
		return nil, nil
	case api.GtfsRealtimeOptions_NYCT_TRIPS:
		inOpts := in.GetNyctTripsOptions()
		return nycttrips.Extension(nycttrips.ExtensionOpts{
			FilterStaleUnassignedTrips: inOpts.GetFilterStaleUnassignedTrips(),
		}), nil
	case api.GtfsRealtimeOptions_NYCT_ALERTS:
		inOpts := in.GetNyctAlertsOptions()
		var outPolicy nyctalerts.ElevatorAlertsDeduplicationPolicy
		switch inOpts.GetElevatorAlertsDeduplicationPolicy() {
		case api.GtfsRealtimeOptions_NyctAlertsOptions_NO_DEDUPLICATION:
			outPolicy = nyctalerts.NoDeduplication
		case api.GtfsRealtimeOptions_NyctAlertsOptions_DEDUPLICATE_IN_STATION:
			outPolicy = nyctalerts.DeduplicateInStation
		case api.GtfsRealtimeOptions_NyctAlertsOptions_DEDUPLICATE_IN_COMPLEX:
			outPolicy = nyctalerts.DeduplicateInComplex
		default:
			return nil, fmt.Errorf("unknown NYCT alerts elevator deduplication policy %s", inOpts.GetElevatorAlertsDeduplicationPolicy())
		}
		return nyctalerts.Extension(nyctalerts.ExtensionOpts{
			ElevatorAlertsDeduplicationPolicy:   outPolicy,
			ElevatorAlertsInformUsingStationIDs: inOpts.GetElevatorAlertsInformUsingStationIds(),
			SkipTimetabledNoServiceAlerts:       inOpts.GetSkipTimetabledNoServiceAlerts(),
			AddNyctMetadata:                     inOpts.GetAddNyctMetadata(),
		}), nil
	default:
		return nil, fmt.Errorf("unknown extension %s", in.Extension)
	}
}
