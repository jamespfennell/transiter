// Package servicemaps contains all of the logic for Transiter's service maps features.
package servicemaps

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"

	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/config"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/graph"
)

// UpdateConfig updates the service map configuration for the provided system.
func UpdateConfig(ctx context.Context, querier db.Querier, systemPk int64, configs []config.ServiceMapConfig) error {
	config, err := querier.ListServiceMapConfigsInSystem(ctx, systemPk)
	if err != nil {
		return nil
	}
	configIDToPk := map[string]int64{}
	for _, config := range config {
		configIDToPk[config.ID] = config.Pk
	}
	for _, newConfig := range configs {
		if pk, ok := configIDToPk[newConfig.ID]; ok {
			if err := querier.UpdateServiceMapConfig(ctx, db.UpdateServiceMapConfigParams{
				Pk:                     pk,
				Config:                 newConfig.MarshalToJSON(),
				DefaultForRoutesAtStop: newConfig.DefaultForRoutesAtStop,
				DefaultForStopsInRoute: newConfig.DefaultForStopsInRoute,
			}); err != nil {
				return err
			}
			delete(configIDToPk, newConfig.ID)
		} else {
			if err := querier.InsertServiceMapConfig(ctx, db.InsertServiceMapConfigParams{
				ID:                     newConfig.ID,
				SystemPk:               systemPk,
				Config:                 newConfig.MarshalToJSON(),
				DefaultForRoutesAtStop: newConfig.DefaultForRoutesAtStop,
				DefaultForStopsInRoute: newConfig.DefaultForStopsInRoute,
			}); err != nil {
				return err
			}
		}
	}
	for _, pk := range configIDToPk {
		if err := querier.DeleteServiceMapConfig(ctx, pk); err != nil {
			return err
		}
	}
	return nil
}

type UpdateStaticMapsArgs struct {
	SystemPk    int64
	Trips       []gtfs.ScheduledTrip
	RouteIDToPk map[string]int64
}

// UpdateStaticMaps updates the static service maps
func UpdateStaticMaps(ctx context.Context, querier db.Querier, args UpdateStaticMapsArgs) error {
	configs, err := ListConfigsInSystem(ctx, querier, args.SystemPk)
	if err != nil {
		return err
	}

	stopIDToStationPk, err := dbwrappers.MapStopIDToStationPk(ctx, querier, args.SystemPk)
	if err != nil {
		return err
	}

	for _, smc := range configs {
		if smc.Config.Source != config.ServiceMapSourceStatic {
			continue
		}
		routePkToStopPks := buildStaticMaps(&smc.Config, args.RouteIDToPk, stopIDToStationPk, args.Trips)
		if err := persistMaps(ctx, querier, &smc, routePkToStopPks); err != nil {
			return err
		}
	}
	return nil
}

func persistMaps(ctx context.Context, querier db.Querier, smc *Config, routePkToStopPks map[int64][]int64) error {
	for routePk, stopPks := range routePkToStopPks {
		if err := querier.DeleteServiceMap(ctx, db.DeleteServiceMapParams{
			ConfigPk: smc.Pk,
			RoutePk:  routePk,
		}); err != nil {
			return err
		}
		// TODO: consider not deleting and then inserting
		mapPk, err := querier.InsertServiceMap(ctx, db.InsertServiceMapParams{
			ConfigPk: smc.Pk,
			RoutePk:  routePk,
		})
		if err != nil {
			return err
		}
		for i, stopPk := range stopPks {
			if err := querier.InsertServiceMapStop(ctx, db.InsertServiceMapStopParams{
				MapPk:    mapPk,
				StopPk:   stopPk,
				Position: int32(i),
			}); err != nil {
				return err
			}
		}
	}
	return nil
}

func buildStaticMaps(smc *config.ServiceMapConfig, routeIDToPk map[string]int64, stopIDToStationPk map[string]int64, trips []gtfs.ScheduledTrip) map[int64][]int64 {
	routePkToEdges := map[int64]map[graph.Edge]bool{}
	for _, routePk := range routeIDToPk {
		routePkToEdges[routePk] = map[graph.Edge]bool{}
	}
	for _, trip := range trips {
		routePk, ok := routeIDToPk[trip.Route.Id]
		if !ok {
			continue
		}
		if trip.DirectionId == nil {
			continue
		}
		// TODO: filter the trip based on the service map config
		directionID := *trip.DirectionId
		for j := 1; j < len(trip.StopTimes); j++ {
			from, to := j-1, j
			if !directionID {
				from, to = j, j-1
			}
			// TODO: what if the stop IDs don't exist?
			routePkToEdges[routePk][graph.Edge{
				FromLabel: stopIDToStationPk[trip.StopTimes[from].Stop.Id],
				ToLabel:   stopIDToStationPk[trip.StopTimes[to].Stop.Id],
			}] = true
		}
	}
	return buildMaps(routePkToEdges)
}

func buildMaps(routePkToEdges map[int64]map[graph.Edge]bool) map[int64][]int64 {
	routePkToStopPks := map[int64][]int64{}
	for routePk, edgesSet := range routePkToEdges {
		var edges []graph.Edge
		for edge := range edgesSet {
			edges = append(edges, edge)
		}
		g := graph.NewGraph(edges...)
		orderedNodes, err := graph.SortBasic(g)
		if err != nil {
			continue
		}
		for _, node := range orderedNodes {
			routePkToStopPks[routePk] = append(routePkToStopPks[routePk], node.GetLabel())
		}
	}
	return routePkToStopPks
}

type Trip struct {
	RoutePk     int64
	DirectionID sql.NullBool
	StopPks     []int64
}

type UpdateRealtimeMapsArgs struct {
	SystemPk      int64
	OldTrips      []Trip
	NewTrips      []Trip
	StaleRoutePks []int64
}

// UpdateRealtimeMaps updates the realtime service maps
func UpdateRealtimeMaps(ctx context.Context, querier db.Querier, args UpdateRealtimeMapsArgs) error {
	stopPksSet := map[int64]bool{}
	var stopPks []int64
	for _, trips := range [][]Trip{args.OldTrips, args.NewTrips} {
		for _, trip := range trips {
			for _, stopPk := range trip.StopPks {
				if !stopPksSet[stopPk] {
					stopPks = append(stopPks, stopPk)
				}
				stopPksSet[stopPk] = true
			}
		}
	}

	stopPkToStationPk, err := dbwrappers.MapStopPkToStationPk(ctx, querier, stopPks)
	if err != nil {
		return err
	}

	routePkToOldEdges := buildRealtimeMapEdges(args.OldTrips, stopPkToStationPk)
	routePkToNewEdges := buildRealtimeMapEdges(args.NewTrips, stopPkToStationPk)
	for routePk, oldEdges := range routePkToOldEdges {
		newEdges := routePkToNewEdges[routePk]
		if graph.EdgeSetsEqual(oldEdges, newEdges) {
			delete(routePkToNewEdges, routePk)
		}
	}
	for _, routePk := range args.StaleRoutePks {
		routePkToNewEdges[routePk] = map[graph.Edge]bool{}
	}

	routePkToStopPks := buildMaps(routePkToNewEdges)
	configs, err := ListConfigsInSystem(ctx, querier, args.SystemPk)
	if err != nil {
		return err
	}
	for _, smc := range configs {
		if smc.Config.Source != config.ServiceMapSourceRealtime {
			continue
		}
		if err := persistMaps(ctx, querier, &smc, routePkToStopPks); err != nil {
			return err
		}
	}
	return nil
}

func buildRealtimeMapEdges(trips []Trip, stopPkToStationPk map[int64]int64) map[int64]map[graph.Edge]bool {
	m := map[int64]map[graph.Edge]bool{}
	for _, trip := range trips {
		if !trip.DirectionID.Valid {
			continue
		}
		if _, ok := m[trip.RoutePk]; !ok {
			m[trip.RoutePk] = map[graph.Edge]bool{}
		}
		for i := 1; i < len(trip.StopPks); i++ {
			var edge graph.Edge
			switch trip.DirectionID.Bool {
			case true:
				edge = graph.Edge{
					FromLabel: stopPkToStationPk[trip.StopPks[i-1]],
					ToLabel:   stopPkToStationPk[trip.StopPks[i]],
				}
			case false:
				edge = graph.Edge{
					FromLabel: stopPkToStationPk[trip.StopPks[i]],
					ToLabel:   stopPkToStationPk[trip.StopPks[i-1]],
				}
			}
			m[trip.RoutePk][edge] = true
		}
	}
	return m
}

type Config struct {
	Pk     int64
	Config config.ServiceMapConfig
}

// ListConfigsInSystem lists all of the service map configs in the provided system
func ListConfigsInSystem(ctx context.Context, querier db.Querier, systemPk int64) ([]Config, error) {
	rawConfigs, err := querier.ListServiceMapConfigsInSystem(ctx, systemPk)
	if err != nil {
		return nil, err
	}
	var configs []Config
	for _, rawConfig := range rawConfigs {
		smc := Config{
			Pk: rawConfig.Pk,
		}
		if err := json.Unmarshal(rawConfig.Config, &smc.Config); err != nil {
			log.Printf("Invalid service map config, skipping: %+v", err)
			continue
		}
		configs = append(configs, smc)
	}
	return configs, nil
}
