package client

import (
	"encoding/json"
	"fmt"
	"github.com/jamespfennell/transiter/tests/performance/stats"
	"io/ioutil"
	"math/rand"
	"net/http"
	"time"
)

type State interface {
	Transition() (State, error)
}

func NewStartState(baseUrl string) State {
	return StartState{baseUrl: baseUrl}
}

type StartState struct {
	baseUrl string
}

func (state StartState) Transition() (State, error) {
	var response RootResponse
	if _, err := get(state.baseUrl, &response); err != nil {
		return state, err
	}
	var listSystemsResponse []ListSystemsResponse
	if _, err := get(response.Systems.Href, &listSystemsResponse); err != nil {
		return state, err
	}
	systemIndex := rand.Intn(len(listSystemsResponse))
	var systemState SystemState
	if _, err := get(listSystemsResponse[systemIndex].Href, &systemState.systemResponse); err != nil {
		return state, err
	}
	return systemState, nil
}

type SystemState struct {
	systemResponse SystemResponse
}

func (state SystemState) Transition() (State, error) {
	var listRoutesResponse []ListRoutesResponse
	if _, err := get(state.systemResponse.Routes.Href, &listRoutesResponse); err != nil {
		return state, err
	}
	routeIndex := rand.Intn(len(listRoutesResponse))
	routeState, err := NewRouteState(listRoutesResponse[routeIndex].Href)
	if err != nil {
		return state, err
	}
	return routeState, nil
}

func NewRouteState(href string) (RouteState, error) {
	var routeState RouteState
	d, err := get(href, &routeState.routeResponse)
	if err != nil {
		stats.RouteStats.AddErr()
	} else {
		stats.RouteStats.Add(routeState.routeResponse.Id, d)
	}
	return routeState, err
}

type RouteState struct {
	routeResponse RouteResponse
}

func (state RouteState) Transition() (State, error) {
	serviceMapIndex := state.selectServiceMap()
	if serviceMapIndex < 0 {
		return EndState{}, nil
	}
	stopIndex := rand.Intn(len(state.routeResponse.Service_maps[serviceMapIndex].Stops))
	stopState, err := NewStopState(state.routeResponse.Service_maps[serviceMapIndex].Stops[stopIndex].Href)
	if err != nil {
		return state, err
	}
	return stopState, nil
}

func (state RouteState) selectServiceMap() int {
	randIndex := rand.Intn(len(state.routeResponse.Service_maps))
	if len(state.routeResponse.Service_maps[randIndex].Stops) > 0 {
		return randIndex
	}
	for i := 0; i < len(state.routeResponse.Service_maps); i++ {
		if len(state.routeResponse.Service_maps[i].Stops) > 0 {
			return i
		}
	}
	return -1
}

func NewStopState(href string) (StopState, error) {
	var stopState StopState
	d, err := get(href, &stopState.stopResponse)
	if err != nil {
		stats.StopStats.AddErr()
	} else {
		stats.StopStats.Add(fmt.Sprintf("%s (%s)", stopState.stopResponse.Name, stopState.stopResponse.Id), d)
	}
	return stopState, err
}

type StopState struct {
	stopResponse StopResponse
}

func (state StopState) Transition() (State, error) {
	n := rand.Intn(3)
	switch {
	case n <= 1:
		return state.TransitionToTrip()
	}
	return EndState{}, nil
}

func (state StopState) TransitionToTrip() (State, error) {
	if len(state.stopResponse.Stop_times) == 0 {
		return EndState{}, nil
	}
	stopTimeIndex := rand.Intn(len(state.stopResponse.Stop_times))
	tripState, err := NewTripState(state.stopResponse.Stop_times[stopTimeIndex].Trip.Href)
	if err != nil {
		return state, err
	}
	return tripState, nil
}

func NewTripState(href string) (State, error) {
	var tripState TripState
	d, err := get(href, &tripState.tripResponse)
	if err != nil {
		stats.TripStats.AddErr()
	} else {
		stats.TripStats.Add(tripState.tripResponse.Id, d)
	}
	return tripState, err
}

type TripState struct {
	tripResponse TripResponse
}

func (state TripState) Transition() (State, error) {
	if len(state.tripResponse.Stop_times) == 0 {
		return EndState{}, nil
	}
	stopTimeIndex := rand.Intn(len(state.tripResponse.Stop_times))
	stopState, err := NewStopState(state.tripResponse.Stop_times[stopTimeIndex].Stop.Href)
	if err != nil {
		return state, err
	}
	return stopState, nil
}

type EndState struct{}

func (state EndState) Transition() (State, error) {
	panic("Can't transition out of the end state")
}

func get(url string, v interface{}) (time.Duration, error) {
	start := time.Now()
	response, err := http.Get(url)
	d := time.Now().Sub(start)
	if err != nil {
		return d, err
	}
	content, err := ioutil.ReadAll(response.Body)
	if err != nil {
		_ = response.Body.Close()
		return d, err
	}
	if err := response.Body.Close(); err != nil {
		return d, err
	}
	return d, json.Unmarshal(content, v)
}

type RootResponse struct {
	Systems struct {
		Count int
		Href  string
	}
}

type ListSystemsResponse struct {
	Id   string
	Name string
	Href string
}

type SystemResponse struct {
	Routes struct {
		Count int
		Href  string
	}
}

type ListRoutesResponse struct {
	Id   string
	Href string
}

type RouteResponse struct {
	Id           string
	Service_maps []struct {
		Group_id string
		Stops    []struct {
			Id   string
			Name string
			Href string
		}
	}
}

type StopResponse struct {
	Id         string
	Name       string
	Stop_times []struct {
		Trip struct {
			Id   string
			Href string
		}
	}
}

type TripResponse struct {
	Id    string
	Route struct {
		Id   string
		Href string
	}
	Stop_times []struct {
		Stop struct {
			Id   string
			Href string
		}
	}
}
