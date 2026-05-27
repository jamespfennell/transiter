package model

import (
	"fmt"
	"io"
	"strconv"
	"time"

	"github.com/99designs/gqlgen/graphql"
)

func MarshalDateTime(t time.Time) graphql.Marshaler {
	return graphql.WriterFunc(func(w io.Writer) {
		io.WriteString(w, strconv.FormatInt(t.Unix(), 10))
	})
}

func UnmarshalDateTime(v interface{}) (time.Time, error) {
	switch v := v.(type) {
	case int64:
		return time.Unix(v, 0), nil
	case int:
		return time.Unix(int64(v), 0), nil
	case float64:
		return time.Unix(int64(v), 0), nil
	case string:
		n, err := strconv.ParseInt(v, 10, 64)
		if err != nil {
			return time.Time{}, fmt.Errorf("DateTime must be a unix timestamp, got %q", v)
		}
		return time.Unix(n, 0), nil
	default:
		return time.Time{}, fmt.Errorf("DateTime must be a unix timestamp, got %T", v)
	}
}

type Location struct {
	Lat float64 `json:"lat"`
	Lon float64 `json:"lon"`
}

type LocationInput struct {
	Lat float64 `json:"lat"`
	Lon float64 `json:"lon"`
}

type Stop struct {
	Pk       int64  `json:"-"`
	SystemPk int64  `json:"-"`
	ID       string `json:"id"`
	Name     *string `json:"name"`
	Location Location `json:"location"`
	Type     StopType `json:"type"`
	ParentStopPk *int64 `json:"-"`
}

type StopTime struct {
	Arrival    TimeEstimate `json:"arrival"`
	Departure  TimeEstimate `json:"departure"`
	Headsign   *string      `json:"headsign"`
	TripPk     int64        `json:"-"`
	RoutePk    int64        `json:"-"`
	TripID     string       `json:"-"`
	DirectionID *bool       `json:"-"`
	RouteCache *Route       `json:"-"`
}

type TimeEstimate struct {
	Time        *time.Time `json:"time"`
	Delay       *int32     `json:"delay"`
	Uncertainty *int32     `json:"uncertainty"`
}

type Trip struct {
	ID          string `json:"id"`
	DirectionID *bool  `json:"directionId"`
	RoutePk     int64  `json:"-"`
	RouteCache  *Route `json:"-"`
}

type Route struct {
	ID        string  `json:"id"`
	Color     string  `json:"color"`
	ShortName *string `json:"shortName"`
	LongName  *string `json:"longName"`
}

type StopType string

const (
	StopTypeStop           StopType = "STOP"
	StopTypeStation        StopType = "STATION"
	StopTypeEntranceOrExit StopType = "ENTRANCE_OR_EXIT"
	StopTypeGenericNode    StopType = "GENERIC_NODE"
	StopTypeBoardingArea   StopType = "BOARDING_AREA"
	StopTypePlatform       StopType = "PLATFORM"
)

func (e StopType) IsValid() bool {
	switch e {
	case StopTypeStop, StopTypeStation, StopTypeEntranceOrExit, StopTypeGenericNode, StopTypeBoardingArea, StopTypePlatform:
		return true
	}
	return false
}

func (e StopType) String() string {
	return string(e)
}

func (e *StopType) UnmarshalGQL(v interface{}) error {
	str, ok := v.(string)
	if !ok {
		return fmt.Errorf("enums must be strings")
	}
	*e = StopType(str)
	if !e.IsValid() {
		return fmt.Errorf("%s is not a valid StopType", str)
	}
	return nil
}

func (e StopType) MarshalGQL(w io.Writer) {
	fmt.Fprint(w, strconv.Quote(e.String()))
}
