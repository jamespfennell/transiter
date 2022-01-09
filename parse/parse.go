package parse

import (
	"context"
)

type Parser interface {
	Parse(ctx context.Context, content []byte) (*Result, error)
}

type Result struct {
	Agencies []Agency
	Routes   []Route
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

type RouteType int32

const (
	Tram       RouteType = 0
	Subway     RouteType = 1
	Rail       RouteType = 2
	Bus        RouteType = 3
	Ferry      RouteType = 4
	CableTram  RouteType = 5
	AerialLift RouteType = 6
	Funicular  RouteType = 7
	TrolleyBus RouteType = 11
	Monorail   RouteType = 12

	// Transiter only value
	UnknownRouteType RouteType = 10000
)

func NewRouteType(i int) (RouteType, bool) {
	var t RouteType
	switch i {
	case 0:
		t = Tram
	case 1:
		t = Subway
	case 2:
		t = Rail
	case 3:
		t = Bus
	case 4:
		t = Ferry
	case 5:
		t = CableTram
	case 6:
		t = AerialLift
	case 7:
		t = Funicular
	case 11:
		t = TrolleyBus
	case 12:
		t = Monorail
	default:
		return UnknownRouteType, false
	}
	return t, true
}

func (t RouteType) String() string {
	switch t {
	case Tram:
		return "TRAM"
	case Subway:
		return "SUBWAY"
	case Rail:
		return "RAIL"
	case Bus:
		return "BUS"
	case Ferry:
		return "FERRY"
	case CableTram:
		return "CABLE_TRAM"
	case AerialLift:
		return "AERIAL_LIFT"
	case Funicular:
		return "FUNICULAR"
	case TrolleyBus:
		return "TROLLEY_BUS"
	case Monorail:
		return "MONORAIL"
	}
	return "UNKNOWN"
}

type RoutePolicy int32

const (
	NotAllowed           RoutePolicy = 0
	Continuous           RoutePolicy = 1
	PhoneAgency          RoutePolicy = 2
	CoordinateWithDriver RoutePolicy = 3
)

func NewRoutePolicy(i int) RoutePolicy {
	var t RoutePolicy
	// TODO: figure out the mismatch here between 0 and 1
	switch i {
	case 0:
		t = Continuous
	case 1:
		t = NotAllowed
	case 2:
		t = PhoneAgency
	case 3:
		t = CoordinateWithDriver
	default:
		t = NotAllowed
	}
	return t
}

func (t RoutePolicy) String() string {
	switch t {
	case Continuous:
		return "ALLOWED"
	case PhoneAgency:
		return "PHONE_AGENCY"
	case CoordinateWithDriver:
		return "COORDINATE_WITH_DRIVER"
	case NotAllowed:
		fallthrough
	default:
		return "NOT_ALLOWED"
	}
}

type Route struct {
	Id                string
	Agency            *Agency
	Color             string
	TextColor         string
	ShortName         *string
	LongName          *string
	Description       *string
	Type              RouteType
	Url               *string
	SortOrder         *int32
	ContinuousPickup  RoutePolicy
	ContinuousDropOff RoutePolicy
}
