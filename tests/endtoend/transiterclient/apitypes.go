package transiterclient

import (
	"encoding/json"
	"strconv"
)

// Int64String provides a way to marshal and unmarshal 64 bit integers as strings.
// This is used to work around the fact that JSON only supports 32 bit integers, so
// Transiter returns 64 bit integers as strings.
type Int64String int64

func (i Int64String) MarshalJSON() ([]byte, error) {
	return json.Marshal(strconv.FormatInt(int64(i), 10))
}

func (i *Int64String) UnmarshalJSON(data []byte) error {
	var jstring string
	err := json.Unmarshal(data, &jstring)
	if err != nil {
		return err
	}
	*(*int64)(i), err = strconv.ParseInt(jstring, 0, 64)
	return err
}

type ChildResources struct {
	Count Int64String `json:"count"`
	Path  string      `json:"path"`
	URL   string      `json:"url,omitempty"`
}

type System struct {
	ID        string          `json:"id"`
	Name      string          `json:"name"`
	Status    string          `json:"status"`
	Agencies  *ChildResources `json:"agencies,omitempty"`
	Feeds     *ChildResources `json:"feeds,omitempty"`
	Routes    *ChildResources `json:"routes,omitempty"`
	Stops     *ChildResources `json:"stops,omitempty"`
	Transfers *ChildResources `json:"transfers,omitempty"`
}

type ListSystemsResponse struct {
	Systems []System `json:"systems"`
}

type Agency struct {
	ID       string           `json:"id"`
	Name     string           `json:"name"`
	URL      string           `json:"url"`
	Timezone string           `json:"timezone"`
	Language *string          `json:"language,omitempty"`
	Phone    *string          `json:"phone,omitempty"`
	FareURL  *string          `json:"fareUrl,omitempty"`
	Email    *string          `json:"email,omitempty"`
	Routes   []RouteReference `json:"routes"`
	Alerts   []AlertReference `json:"alerts"`
}

type AgencyResponse struct {
	Agencies []Agency `json:"agencies"`
}

type FeedUpdateResponse struct {
	FeedUpdate FeedUpdate `json:"feedUpdate"`
}

type Stop struct {
	ID                 string             `json:"id"`
	Code               string             `json:"code"`
	Name               string             `json:"name"`
	Description        string             `json:"description"`
	ZoneID             string             `json:"zoneId"`
	Latitude           float64            `json:"latitude"`
	Longitude          float64            `json:"longitude"`
	URL                string             `json:"url"`
	Type               string             `json:"type"`
	WheelchairBoarding bool               `json:"wheelchairBoarding"`
	Timezone           string             `json:"timezone"`
	PlatformCode       string             `json:"platformCode"`
	ParentStop         *StopReference     `json:"parentStop,omitempty"`
	ChildStops         []StopReference    `json:"childStops"`
	Transfers          []Transfer         `json:"transfers"`
	ServiceMaps        []ServiceMapAtStop `json:"serviceMaps"`
	Alerts             []AlertReference   `json:"alerts"`
	StopTimes          []StopTime         `json:"stopTimes"`
}

type StopReference struct {
	ID string `json:"id"`
}

type ListStopsResponse struct {
	Stops  []Stop  `json:"stops"`
	NextID *string `json:"nextId,omitempty"`
}

type EstimatedTime struct {
	Time Int64String `json:"time"`
}

type StopTime struct {
	Trip         *TripReference `json:"trip"`
	Arrival      *EstimatedTime `json:"arrival"`
	Departure    *EstimatedTime `json:"departure"`
	StopSequence *uint32        `json:"stopSequence"`
	Future       bool           `json:"future"`
	Headsign     *string        `json:"headsign,omitempty"`
}

type Route struct {
	ID                string              `json:"id"`
	ShortName         string              `json:"shortName"`
	LongName          string              `json:"longName"`
	Color             string              `json:"color"`
	TextColor         string              `json:"textColor"`
	Description       string              `json:"description"`
	URL               string              `json:"url"`
	SortOrder         int                 `json:"sortOrder"`
	ContinuousPickup  string              `json:"continuousPickup"`
	ContinuousDropOff string              `json:"continuousDropOff"`
	Type              string              `json:"type"`
	ServiceMaps       []ServiceMapInRoute `json:"serviceMaps"`
	Alerts            []AlertReference    `json:"alerts"`
}

type RouteReference struct {
	ID string `json:"id"`
}

type ListRoutesResponse struct {
	Routes []Route `json:"routes"`
}

type Trip struct {
	ID        string            `json:"id"`
	Shape     *ShapeReference   `json:"shape"`
	Vehicle   *VehicleReference `json:"vehicle"`
	StopTimes []StopTime        `json:"stopTimes"`
	Alerts    []AlertReference  `json:"alerts"`
}

type TripReference struct {
	ID          string         `json:"id"`
	Route       RouteReference `json:"route"`
	DirectionID bool           `json:"directionId"`
}

type ListTripsResponse struct {
	Trips []Trip `json:"trips"`
}

type Transfer struct {
	ID              string         `json:"id"`
	FromStop        *StopReference `json:"fromStop"`
	ToStop          *StopReference `json:"toStop"`
	Type            string         `json:"type"`
	MinTransferTime int32          `json:"minTransferTime"`
}

type ListTransfersResponse struct {
	Transfers []Transfer `json:"transfers"`
}

type FeedUpdate struct {
	Status string `json:"status"`
}

type AlertActivePeriod struct {
	StartsAt Int64String `json:"startsAt"`
	EndsAt   Int64String `json:"endsAt"`
}

type AlertText struct {
	Text     string `json:"text"`
	Language string `json:"language"`
}

type Alert struct {
	ID                  string              `json:"id"`
	Cause               string              `json:"cause"`
	Effect              string              `json:"effect"`
	CurrentActivePeriod AlertActivePeriod   `json:"currentActivePeriod"`
	AllActivePeriods    []AlertActivePeriod `json:"allActivePeriods"`
	Header              []AlertText         `json:"header"`
	Description         []AlertText         `json:"description"`
	URL                 []AlertText         `json:"url"`
}

type AlertReference struct {
	ID     string `json:"id"`
	Cause  string `json:"cause"`
	Effect string `json:"effect"`
}

type ListAlertsResponse struct {
	Alerts []Alert `json:"alerts"`
}

type ShapePoint struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Distance  float64 `json:"distance"`
}

type Shape struct {
	ID     string       `json:"id"`
	Points []ShapePoint `json:"points"`
}

type ShapeReference struct {
	ID string `json:"id"`
}

type ListShapesResponse struct {
	Shapes []Shape `json:"shapes"`
	NextID *string `json:"nextId,omitempty"`
}

type Vehicle struct {
	ID        string         `json:"id"`
	Trip      *TripReference `json:"trip"`
	Latitude  float64        `json:"latitude"`
	Longitude float64        `json:"longitude"`
}

type VehicleReference struct {
	ID string `json:"id"`
}

type ListVehiclesResponse struct {
	Vehicles []Vehicle `json:"vehicles"`
	NextID   *string   `json:"nextId,omitempty"`
}

type ServiceMapAtStop struct {
	ConfigID string           `json:"configId"`
	Routes   []RouteReference `json:"routes"`
}

type ServiceMapInRoute struct {
	ConfigID string          `json:"configId"`
	Stops    []StopReference `json:"stops"`
}

type Feed struct {
	ID                     string       `json:"id"`
	LastSuccessfulUpdateMs *Int64String `json:"lastSuccessfulUpdateMs,omitempty"`
	LastSkippedUpdateMs    *Int64String `json:"lastSkippedUpdateMs,omitempty"`
	LastFailedUpdateMs     *Int64String `json:"lastFailedUpdateMs,omitempty"`
}

type ListFeedsResponse struct {
	Feeds []Feed `json:"feeds"`
}
