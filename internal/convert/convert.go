// Package convert contains type converters.
package convert

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"math/big"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/gtfs/extensions"
	"github.com/jamespfennell/gtfs/extensions/nyctalerts"
	"github.com/jamespfennell/gtfs/extensions/nyctbustrips"
	"github.com/jamespfennell/gtfs/extensions/nycttrips"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"golang.org/x/exp/slog"
)

func SQLNullTime(t pgtype.Timestamptz) *int64 {
	if !t.Valid {
		return nil
	}
	r := t.Time.Unix()
	return &r
}

func SQLNullString(t pgtype.Text) *string {
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

func SQLNullInt64(t pgtype.Int8) *int64 {
	if !t.Valid {
		return nil
	}
	return &t.Int64
}

func SQLNullInt32(t pgtype.Int4) *int32 {
	if !t.Valid {
		return nil
	}
	return &t.Int32
}

func NullInt32(t *int32) pgtype.Int4 {
	if t == nil {
		return pgtype.Int4{}
	}
	return pgtype.Int4{Valid: true, Int32: *t}
}

func NullInt64(t *int64) pgtype.Int8 {
	if t == nil {
		return pgtype.Int8{}
	}
	return pgtype.Int8{Valid: true, Int64: *t}
}

func NullFloat64(t *float64) pgtype.Float8 {
	if t == nil {
		return pgtype.Float8{}
	}
	return pgtype.Float8{Valid: true, Float64: *t}
}

func NullString(t *string) pgtype.Text {
	if t == nil {
		return pgtype.Text{}
	}
	return pgtype.Text{Valid: true, String: *t}
}

func NullBool(t *bool) pgtype.Bool {
	if t == nil {
		return pgtype.Bool{}
	}
	return pgtype.Bool{Valid: true, Bool: *t}
}

func SQLNullBool(t pgtype.Bool) *bool {
	if !t.Valid {
		return nil
	}
	return &t.Bool
}

func Gps(f *float64) pgtype.Numeric {
	if f == nil {
		return pgtype.Numeric{}
	}
	return pgtype.Numeric{
		Int:   big.NewInt(int64(*f * 1000000)),
		Exp:   -6,
		Valid: true,
	}
}

func SQLGps(n pgtype.Numeric) *float64 {
	if !n.Valid {
		return nil
	}
	f := float64(n.Int.Int64()) / 1000000
	return &f
}

func DirectionID(d gtfs.DirectionID) pgtype.Bool {
	switch d {
	case gtfs.DirectionIDFalse:
		return pgtype.Bool{
			Valid: true,
			Bool:  false,
		}
	case gtfs.DirectionIDTrue:
		return pgtype.Bool{
			Valid: true,
			Bool:  true,
		}
	default:
		return pgtype.Bool{
			Valid: false,
		}
	}
}

func NullTime(t *time.Time) pgtype.Timestamptz {
	if t == nil {
		return pgtype.Timestamptz{}
	}
	return pgtype.Timestamptz{
		Valid: true,
		Time:  *t,
	}
}

func NullDuration(d *time.Duration) pgtype.Int4 {
	if d == nil {
		return pgtype.Int4{}
	}
	return pgtype.Int4{
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

func FeedUpdateResult(logger *slog.Logger, result pgtype.Text) *api.FeedUpdate_Result {
	if !result.Valid {
		return nil
	}
	if i, ok := api.FeedUpdate_Result_value[result.String]; ok {
		return api.FeedUpdate_Result(i).Enum()
	}
	logger.Error(fmt.Sprintf("unknown feed update result %s", result.String))
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
			PreserveMTrainPlatformsInBushwick: inOpts.GetPreserveMTrainPlatformsInBushwick(),
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
	case api.GtfsRealtimeOptions_NYCT_BUS_TRIPS:
		return nyctbustrips.Extension(), nil
	default:
		return nil, fmt.Errorf("unknown extension %s", in.Extension)
	}
}
