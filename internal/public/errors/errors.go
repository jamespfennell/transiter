// Package errors contains logic for making errors user-friendly at the API boundary.
package errors

import (
	"context"
	"fmt"
	"net/http"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"golang.org/x/exp/slog"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type publicErr struct {
	*status.Status
}

func (e publicErr) Error() string {
	return e.Status.String()
}

func (e publicErr) GRPCStatus() *status.Status {
	return e.Status
}

// NewNotFoundError returns a not found error.
//
// This will be mapped to a 404 error in the API.
func NewNotFoundError(msg string) error {
	return publicErr{
		Status: status.New(codes.NotFound, msg),
	}
}

// NewInvalidArgumentError returns an invalid argument error.
//
// This will be mapped to a 400 error in the API.
func NewInvalidArgumentError(msg string) error {
	return publicErr{
		Status: status.New(codes.InvalidArgument, msg),
	}
}

func GetStatusCode(err error) codes.Code {
	if err == nil {
		return codes.OK
	}
	if s, ok := err.(interface {
		GRPCStatus() *status.Status
	}); ok {
		return s.GRPCStatus().Code()
	}
	return codes.Unknown
}

// ServeMuxOption returns a `runtime.ServeMuxOption` that makes errors user-friendly at the API boundary.
func ServeMuxOption(logger *slog.Logger) runtime.ServeMuxOption {
	return runtime.WithErrorHandler(func(ctx context.Context, sm *runtime.ServeMux, m runtime.Marshaler, w http.ResponseWriter, r *http.Request, err error) {
		switch err.(type) {
		case publicErr:
			// nothing to do
		case interface {
			GRPCStatus() *status.Status
		}:
			// nothing to do
		default:
			logger.ErrorCtx(ctx, fmt.Sprintf("unexpected internal error: %s", err))
			s := status.New(codes.Internal, "internal error")
			s, _ = s.WithDetails(status.Convert(err).Proto())
			err = publicErr{
				Status: s,
			}
		}
		logger.DebugCtx(ctx, fmt.Sprintf("returning API error: %s", err))
		runtime.DefaultHTTPErrorHandler(ctx, sm, m, w, r, err)
	})
}
