// Package transiterclient provides an HTTP client for the Transiter API.
package transiterclient

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type TransiterClient struct {
	// Currently active host
	host string
	// Host for the admin and public APIs
	adminHost string
	// Host for the public APIs
	publicHost string
}

func NewTransiterClient(adminHost string, publicHost string) *TransiterClient {
	trimmedAdminHost := strings.TrimSuffix(adminHost, "/")
	trimmedPublicHost := strings.TrimSuffix(publicHost, "/")
	return &TransiterClient{
		host:       trimmedAdminHost,
		adminHost:  trimmedAdminHost,
		publicHost: trimmedPublicHost,
	}
}

func (c *TransiterClient) UseAdminHost() {
	c.host = c.adminHost
}

func (c *TransiterClient) UsePublicHost() {
	c.host = c.publicHost
}

type QueryParam struct {
	Key   string
	Value string
}

func (c *TransiterClient) PingUntilOK(numTries int) error {
	var lastErr error
	for i := 0; i < numTries; i++ {
		_, err := get[any](c, "/")
		if err == nil {
			return nil
		}
		lastErr = err
		time.Sleep(500 * time.Millisecond)
	}
	return lastErr
}

func (c *TransiterClient) InstallSystem(systemID string, systemConfig string) error {
	_, err := c.put(fmt.Sprintf("/systems/%s", systemID), map[string]any{
		"yaml_config": map[string]any{
			"content": systemConfig,
		},
	})
	if err != nil {
		return err
	}
	var lastStatus *string
	for i := 0; i < 100; i++ {
		system, err := c.GetSystem(systemID)
		if err != nil {
			return err
		}
		lastStatus = &system.Status
		if system.Status != "INSTALLING" && system.Status != "UPDATING" {
			break
		}
		time.Sleep(50 * time.Millisecond)
	}
	if lastStatus == nil || *lastStatus != "ACTIVE" {
		return fmt.Errorf("system %s is not active", systemID)
	}
	return nil
}

func (c *TransiterClient) PerformFeedUpdate(systemID string, feedID string) error {
	update, err := post[FeedUpdateResponse](c, fmt.Sprintf("/systems/%s/feeds/%s", systemID, feedID), nil)
	if err != nil {
		return err
	}
	if update.FeedUpdate.Status != "UPDATED" && update.FeedUpdate.Status != "SKIPPED" {
		return fmt.Errorf("feed update failed with status %s", update.FeedUpdate.Status)
	}
	return nil
}

func (c *TransiterClient) ListSystems() (*ListSystemsResponse, error) {
	return get[ListSystemsResponse](c, "/systems")
}

func (c *TransiterClient) GetSystem(systemID string) (*System, error) {
	system, err := get[System](c, fmt.Sprintf("/systems/%s", systemID))
	if err != nil {
		return nil, err
	}
	return system, nil
}

func (c *TransiterClient) DeleteSystem(systemID string) error {
	_, err := c.delete(fmt.Sprintf("/systems/%s", systemID))
	if err != nil {
		return err
	}
	return nil
}

func (c *TransiterClient) ListAgencies(systemID string) (*AgencyResponse, error) {
	return get[AgencyResponse](c, fmt.Sprintf("/systems/%s/agencies", systemID))
}

func (c *TransiterClient) GetAgency(systemID string, agencyID string) (*Agency, error) {
	return get[Agency](c, fmt.Sprintf("/systems/%s/agencies/%s", systemID, agencyID))
}

func (c *TransiterClient) ListRoutes(systemID string, params ...QueryParam) (*ListRoutesResponse, error) {
	return get[ListRoutesResponse](c, fmt.Sprintf("/systems/%s/routes", systemID), params...)
}

func (c *TransiterClient) GetRoute(systemID string, routeID string, params ...QueryParam) (*Route, error) {
	return get[Route](c, fmt.Sprintf("/systems/%s/routes/%s", systemID, routeID), params...)
}

func (c *TransiterClient) ListStops(systemID string, params ...QueryParam) (*ListStopsResponse, error) {
	return get[ListStopsResponse](c, fmt.Sprintf("/systems/%s/stops", systemID), params...)
}

func (c *TransiterClient) GetStop(systemID string, stopID string, params ...QueryParam) (*Stop, error) {
	return get[Stop](c, fmt.Sprintf("/systems/%s/stops/%s", systemID, stopID), params...)
}

func (c *TransiterClient) ListTrips(systemID string, routeID string) (*ListTripsResponse, error) {
	return get[ListTripsResponse](c, fmt.Sprintf("/systems/%s/routes/%s/trips", systemID, routeID))
}

func (c *TransiterClient) GetTrip(systemID string, routeID string, tripID string) (*Trip, error) {
	return get[Trip](c, fmt.Sprintf("/systems/%s/routes/%s/trips/%s", systemID, routeID, tripID))
}

func (c *TransiterClient) ListAlerts(systemID string) (*ListAlertsResponse, error) {
	return get[ListAlertsResponse](c, fmt.Sprintf("/systems/%s/alerts", systemID))
}

func (c *TransiterClient) GetAlert(systemID string, alertID string) (*Alert, error) {
	return get[Alert](c, fmt.Sprintf("/systems/%s/alerts/%s", systemID, alertID))
}

func (c *TransiterClient) ListTransfers(systemID string, params ...QueryParam) (*ListTransfersResponse, error) {
	return get[ListTransfersResponse](c, fmt.Sprintf("/systems/%s/transfers", systemID), params...)
}

func (c *TransiterClient) GetTransfer(systemID string, transferID string) (*Transfer, error) {
	return get[Transfer](c, fmt.Sprintf("/systems/%s/transfers/%s", systemID, transferID))
}

func (c *TransiterClient) ListShapes(systemID string, params ...QueryParam) (*ListShapesResponse, error) {
	return get[ListShapesResponse](c, fmt.Sprintf("/systems/%s/shapes", systemID), params...)
}

func (c *TransiterClient) GetShape(systemID string, shapeID string) (*Shape, error) {
	return get[Shape](c, fmt.Sprintf("/systems/%s/shapes/%s", systemID, shapeID))
}

func (c *TransiterClient) ListVehicles(systemID string, params ...QueryParam) (*ListVehiclesResponse, error) {
	return get[ListVehiclesResponse](c, fmt.Sprintf("/systems/%s/vehicles", systemID), params...)
}

func (c *TransiterClient) GetVehicle(systemID string, vehicleID string) (*Vehicle, error) {
	return get[Vehicle](c, fmt.Sprintf("/systems/%s/vehicles/%s", systemID, vehicleID))
}

func (c *TransiterClient) GetFeed(systemID string, feedID string) (*Feed, error) {
	return get[Feed](c, fmt.Sprintf("/systems/%s/feeds/%s", systemID, feedID))
}

func (c *TransiterClient) ListFeeds(systemID string) (*ListFeedsResponse, error) {
	return get[ListFeedsResponse](c, fmt.Sprintf("/systems/%s/feeds", systemID))
}

func get[T any](client *TransiterClient, path string, params ...QueryParam) (*T, error) {
	req, err := http.NewRequest("GET", client.host+path, nil)
	if err != nil {
		return nil, err
	}
	q := req.URL.Query()
	for _, param := range params {
		q.Add(param.Key, param.Value)
	}
	req.URL.RawQuery = q.Encode()

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP request failed with status %d: %s", resp.StatusCode, string(body))
	}
	var responsePayload T
	if err := json.NewDecoder(resp.Body).Decode(&responsePayload); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}
	return &responsePayload, nil
}

func post[T any](client *TransiterClient, path string, body any) (*T, error) {
	jsonBody, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequest("POST", client.host+path, bytes.NewBuffer(jsonBody))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP request failed with status %d", resp.StatusCode)
	}
	var responsePayload T
	if err := json.NewDecoder(resp.Body).Decode(&responsePayload); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}
	return &responsePayload, nil
}

func (c *TransiterClient) put(path string, body any) (*http.Response, error) {
	jsonBody, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequest("PUT", c.host+path, bytes.NewBuffer(jsonBody))
	if err != nil {
		return nil, err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP request failed with status %d", resp.StatusCode)
	}
	return resp, nil
}

func (c *TransiterClient) delete(path string) (*http.Response, error) {
	req, err := http.NewRequest("DELETE", c.host+path, nil)
	if err != nil {
		return nil, err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusNotFound {
		return nil, fmt.Errorf("HTTP request failed with status %d", resp.StatusCode)
	}
	return resp, nil
}
