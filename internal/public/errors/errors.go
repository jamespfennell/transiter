// Package errors contains logic for making errors user-friendly at the API boundary.
package errors

import (
	"context"
	"log"
	"net/http"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
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

// ServeMuxOption returns a `runtime.ServeMuxOption` that makes errors user-friendly at the API boundary.
func ServeMuxOption() runtime.ServeMuxOption {
	return runtime.WithErrorHandler(errorHandler)
}

func errorHandler(ctx context.Context, mux *runtime.ServeMux, m runtime.Marshaler, w http.ResponseWriter, req *http.Request, err error) {
	switch err.(type) {
	case publicErr:
		// nothing to do
	case interface {
		GRPCStatus() *status.Status
	}:
		// nothing to do
	default:
		log.Printf("Unexpected internal error: %s\n", err)
		s := status.New(codes.Internal, "internal error")
		s, _ = s.WithDetails(status.Convert(err).Proto())
		err = publicErr{
			Status: s,
		}
	}
	runtime.DefaultHTTPErrorHandler(ctx, mux, m, w, req, err)
}
