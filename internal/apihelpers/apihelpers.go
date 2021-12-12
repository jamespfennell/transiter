package apihelpers

import (
	"context"
	"database/sql"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/jamespfennell/transiter/internal/service/errors"
	"google.golang.org/protobuf/encoding/protojson"
	"net/http"
)

// TODO(APIv2): rename X-Transiter-BaseURL
const XTransiterHost = "X-Transiter-Host"

func ConvertSqlNullTime(t sql.NullTime) *int64 {
	if !t.Valid {
		return nil
	}
	r := t.Time.Unix()
	return &r
}

func ConvertSqlNullString(t sql.NullString) *string {
	if !t.Valid {
		return nil
	}
	return &t.String
}

func ConvertSqlNullFloat64(t sql.NullFloat64) *float64 {
	if !t.Valid {
		return nil
	}
	return &t.Float64
}

func ConvertSqlNullInt32(t sql.NullInt32) *int32 {
	if !t.Valid {
		return nil
	}
	return &t.Int32
}

func ConvertNullInt32(t *int32) sql.NullInt32 {
	if t == nil {
		return sql.NullInt32{}
	}
	return sql.NullInt32{Valid: true, Int32: *t}
}

func MarshalerOptions() runtime.ServeMuxOption {
	return runtime.WithMarshalerOption("*", &runtime.JSONPb{
		MarshalOptions: protojson.MarshalOptions{
			Indent:          "  ",
			Multiline:       true,
			EmitUnpopulated: true,
		}})
}

func ErrorHandler() runtime.ServeMuxOption {
	return runtime.WithErrorHandler(func(
		ctx context.Context, mux *runtime.ServeMux, m runtime.Marshaler,
		w http.ResponseWriter, req *http.Request, err error) {
		runtime.DefaultHTTPErrorHandler(ctx, mux, m, w, req, errors.ProcessError(err))
	})
}

func IncomingHeaderMatcher() runtime.ServeMuxOption {
	return runtime.WithIncomingHeaderMatcher(
		func(key string) (string, bool) {
			switch key {
			case XTransiterHost:
				return key, true
			default:
				return runtime.DefaultHeaderMatcher(key)
			}
		})
}
