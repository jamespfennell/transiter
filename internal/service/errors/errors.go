package errors

import (
	"log"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type err struct {
	*status.Status
}

func (e err) Error() string {
	return e.Status.String()
}

func (e err) GRPCStatus() *status.Status {
	return e.Status
}

func NewNotFoundError(msg string) error {
	return err{
		Status: status.New(codes.NotFound, msg),
	}
}

func ProcessError(e error) error {
	if _, ok := e.(err); ok {
		return e
	}
	if _, ok := e.(interface {
		GRPCStatus() *status.Status
	}); ok {
		return e
	}
	log.Printf("Unexpected internal error: %s\n", e)
	s := status.New(codes.Internal, "internal error")
	s, _ = s.WithDetails(status.Convert(e).Proto())
	return err{
		Status: s,
	}
}
