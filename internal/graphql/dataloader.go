package graphql

import (
	"context"
	"net/http"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	db "github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/graphql/model"
	"github.com/vikstrous/dataloadgen"
)

type ctxKey struct{}

type Loaders struct {
	ChildStops *dataloadgen.Loader[int64, []*model.Stop]
	ParentStop *dataloadgen.Loader[int64, *model.Stop]
	StopTimes  *dataloadgen.Loader[int64, []*model.StopTime]
}

func DataloaderMiddleware(pool *pgxpool.Pool) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			loaders := &Loaders{
				ChildStops: dataloadgen.NewLoader(newChildStopsLoader(pool)),
				ParentStop: dataloadgen.NewLoader(newParentStopLoader(pool)),
				StopTimes:  dataloadgen.NewLoader(newStopTimesLoader(pool)),
			}
			ctx := context.WithValue(r.Context(), ctxKey{}, loaders)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func getLoaders(ctx context.Context) *Loaders {
	return ctx.Value(ctxKey{}).(*Loaders)
}

// --- child stops loader ---

func newChildStopsLoader(pool *pgxpool.Pool) func(ctx context.Context, keys []int64) ([][]*model.Stop, []error) {
	return func(ctx context.Context, keys []int64) ([][]*model.Stop, []error) {
		results := make([][]*model.Stop, len(keys))
		errs := make([]error, len(keys))

		err := pgx.BeginTxFunc(ctx, pool, pgx.TxOptions{AccessMode: pgx.ReadOnly}, func(tx pgx.Tx) error {
			querier := db.New(tx)
			childRows, err := querier.MapStopPkToChildPks(ctx, keys)
			if err != nil {
				return err
			}
			if len(childRows) == 0 {
				return nil
			}

			parentToChildPks := map[int64][]int64{}
			var allChildPks []int64
			for _, row := range childRows {
				if row.ParentPk.Valid {
					parentToChildPks[row.ParentPk.Int64] = append(parentToChildPks[row.ParentPk.Int64], row.ChildPk)
					allChildPks = append(allChildPks, row.ChildPk)
				}
			}

			children, err := querier.ListStopsByPk(ctx, allChildPks)
			if err != nil {
				return err
			}
			childByPk := map[int64]*db.ListStopsByPkRow{}
			for i := range children {
				childByPk[children[i].Pk] = &children[i]
			}

			for i, key := range keys {
				var stops []*model.Stop
				for _, cpk := range parentToChildPks[key] {
					if c, ok := childByPk[cpk]; ok {
						s := &model.Stop{Pk: c.Pk, ID: c.StopID, Type: model.StopTypeStop}
						if c.Name.Valid {
							s.Name = &c.Name.String
						}
						stops = append(stops, s)
					}
				}
				if stops == nil {
					stops = []*model.Stop{}
				}
				results[i] = stops
			}
			return nil
		})
		if err != nil {
			for i := range errs {
				errs[i] = err
			}
		}
		return results, errs
	}
}

// --- parent stop loader ---

func newParentStopLoader(pool *pgxpool.Pool) func(ctx context.Context, keys []int64) ([]*model.Stop, []error) {
	return func(ctx context.Context, keys []int64) ([]*model.Stop, []error) {
		results := make([]*model.Stop, len(keys))
		errs := make([]error, len(keys))

		err := pgx.BeginTxFunc(ctx, pool, pgx.TxOptions{AccessMode: pgx.ReadOnly}, func(tx pgx.Tx) error {
			querier := db.New(tx)
			rows, err := querier.ListStopsByPk(ctx, keys)
			if err != nil {
				return err
			}
			byPk := map[int64]*db.ListStopsByPkRow{}
			for i := range rows {
				byPk[rows[i].Pk] = &rows[i]
			}
			for i, key := range keys {
				if r, ok := byPk[key]; ok {
					s := &model.Stop{Pk: r.Pk, ID: r.StopID, Type: model.StopTypeStop}
					if r.Name.Valid {
						s.Name = &r.Name.String
					}
					results[i] = s
				}
			}
			return nil
		})
		if err != nil {
			for i := range errs {
				errs[i] = err
			}
		}
		return results, errs
	}
}

// --- stop times loader ---

func newStopTimesLoader(pool *pgxpool.Pool) func(ctx context.Context, keys []int64) ([][]*model.StopTime, []error) {
	return func(ctx context.Context, keys []int64) ([][]*model.StopTime, []error) {
		results := make([][]*model.StopTime, len(keys))
		errs := make([]error, len(keys))

		err := pgx.BeginTxFunc(ctx, pool, pgx.TxOptions{AccessMode: pgx.ReadOnly}, func(tx pgx.Tx) error {
			querier := db.New(tx)

			// 1. Expand each key to include descendants
			descendentRows, err := querier.MapStopPkToDescendentPks(ctx, keys)
			if err != nil {
				return err
			}
			descendantToAncestors := map[int64][]int64{}
			allStopPks := make(map[int64]bool)
			for _, key := range keys {
				allStopPks[key] = true
				descendantToAncestors[key] = append(descendantToAncestors[key], key)
			}
			for _, row := range descendentRows {
				allStopPks[row.DescendentStopPk] = true
				descendantToAncestors[row.DescendentStopPk] = append(descendantToAncestors[row.DescendentStopPk], row.RootStopPk)
			}

			var stopPkSlice []int64
			for pk := range allStopPks {
				stopPkSlice = append(stopPkSlice, pk)
			}

			// 2. Fetch all stop times in one query
			rows, err := querier.ListTripStopTimesByStops(ctx, stopPkSlice)
			if err != nil {
				return err
			}

			// 3. Batch-load routes
			routePkSet := map[int64]bool{}
			for _, row := range rows {
				routePkSet[row.RoutePk] = true
			}
			var routePks []int64
			for pk := range routePkSet {
				routePks = append(routePks, pk)
			}
			routeRows, err := querier.ListRoutesByPk(ctx, routePks)
			if err != nil {
				return err
			}
			routeMap := map[int64]*model.Route{}
			for _, rr := range routeRows {
				routeMap[rr.Pk] = &model.Route{ID: rr.ID, Color: rr.Color}
			}

			// 4. Distribute stop times to ancestor keys
			keyToStopTimes := map[int64][]*model.StopTime{}
			for _, row := range rows {
				st := rowToStopTime(row, routeMap)
				for _, ancestor := range descendantToAncestors[row.StopPk] {
					keyToStopTimes[ancestor] = append(keyToStopTimes[ancestor], st)
				}
			}

			for i, key := range keys {
				sts := keyToStopTimes[key]
				if sts == nil {
					sts = []*model.StopTime{}
				}
				results[i] = sts
			}
			return nil
		})
		if err != nil {
			for i := range errs {
				errs[i] = err
			}
		}
		return results, errs
	}
}

func rowToStopTime(row db.ListTripStopTimesByStopsRow, routeMap map[int64]*model.Route) *model.StopTime {
	st := &model.StopTime{
		Arrival: model.TimeEstimate{
			Time:        timestamptzToPtr(row.ArrivalTime),
			Delay:       int4ToPtr(row.ArrivalDelay),
			Uncertainty: int4ToPtr(row.ArrivalUncertainty),
		},
		Departure: model.TimeEstimate{
			Time:        timestamptzToPtr(row.DepartureTime),
			Delay:       int4ToPtr(row.DepartureDelay),
			Uncertainty: int4ToPtr(row.DepartureUncertainty),
		},
		TripPk:  row.TripPk,
		RoutePk: row.RoutePk,
		TripID:  row.ID,
	}
	if row.Headsign.Valid {
		h := row.Headsign.String
		st.Headsign = &h
	} else if row.ScheduledTripHeadsign.Valid {
		h := row.ScheduledTripHeadsign.String
		st.Headsign = &h
	}
	if row.DirectionID.Valid {
		d := row.DirectionID.Bool
		st.DirectionID = &d
	}
	if route, ok := routeMap[row.RoutePk]; ok {
		st.RouteCache = route
	}
	return st
}
