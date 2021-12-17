package parse

import "context"

type Parser interface {
	Parse(ctx context.Context, content []byte) (*Result, error)
}

type Result struct {
	Agencies []Agency
}

type Agency struct {
	Id       string
	Name     string
	Url      string
	Timezone string
	Language *string
	Phone    *string
	FareUrl  *string
	Email    *string
}
