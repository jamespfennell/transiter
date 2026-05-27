package model

import (
	"fmt"
	"io"
	"strconv"
)

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
	Time        *int64 `json:"time"`
	Delay       *int32 `json:"delay"`
	Uncertainty *int32 `json:"uncertainty"`
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
