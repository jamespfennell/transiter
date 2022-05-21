// Package admin contains the implementation of the Transiter admin API.
package admin

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"text/template"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/config"
	"github.com/jamespfennell/transiter/internal/db/constants"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/scheduler"
	"github.com/jamespfennell/transiter/internal/servicemaps"
	"github.com/jamespfennell/transiter/internal/update"
)

// Service implements the Transiter admin API.
type Service struct {
	pool      *pgxpool.Pool
	scheduler *scheduler.Scheduler
}

func New(pool *pgxpool.Pool, scheduler *scheduler.Scheduler) *Service {
	return &Service{
		pool:      pool,
		scheduler: scheduler,
	}
}

func (s *Service) GetSystemConfig(ctx context.Context, req *api.GetSystemConfigRequest) (*api.SystemConfig, error) {
	reply := &api.SystemConfig{}
	err := s.pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		system, err := querier.GetSystem(ctx, req.SystemId)
		if err != nil {
			if err == pgx.ErrNoRows {
				err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
			}
			return err
		}
		reply.Name = system.Name
		feeds, err := querier.ListFeedsInSystem(ctx, system.Pk)
		if err != nil {
			return err
		}
		for _, feed := range feeds {
			feed := feed
			var feedConfig config.FeedConfig
			if err := json.Unmarshal([]byte(feed.Config), &feedConfig); err != nil {
				return err
			}
			reply.Feeds = append(reply.Feeds, config.ConvertFeedConfig(&feedConfig))
		}
		return nil
	})
	return reply, err
}

func (s *Service) InstallOrUpdateSystem(ctx context.Context, req *api.InstallOrUpdateSystemRequest) (*api.InstallOrUpdateSystemReply, error) {
	log.Printf("Recieved install or update request for system %q", req.SystemId)

	var err error
	var systemConfig *config.SystemConfig
	switch c := req.GetConfig().(type) {
	case *api.InstallOrUpdateSystemRequest_SystemConfig:
		systemConfig = config.ConvertAPISystemConfig(c.SystemConfig)
	case *api.InstallOrUpdateSystemRequest_YamlConfig:
		var rawConfig []byte
		switch s := c.YamlConfig.Source.(type) {
		case *api.YamlConfig_Url:
			rawConfig, err = getRawSystemConfigFromURL(s.Url)
			if err != nil {
				return nil, err
			}
		case *api.YamlConfig_Content:
			rawConfig = []byte(s.Content)
		default:
			return nil, fmt.Errorf("no system configuration provided")
		}
		systemConfig, err = parseSystemConfigYaml(rawConfig, c.YamlConfig.GetIsTemplate(), c.YamlConfig.GetTemplateArgs())
		if err != nil {
			return nil, err
		}
	default:
		return nil, fmt.Errorf("no system configuration provided")
	}
	log.Printf("Config for install/update for system %s:\n%+v\n", req.SystemId, systemConfig)

	if req.Synchronous {
		if err := s.pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
			querier := db.New(tx)
			keepGoing, err := beginSystemInstall(ctx, querier, req.SystemId, systemConfig.Name, req.InstallOnly)
			if err != nil {
				return err
			}
			if !keepGoing {
				return nil
			}
			err = performSystemInstall(ctx, querier, req.SystemId, systemConfig)
			if err := finishSystemInstall(ctx, querier, req.SystemId, err); err != nil {
				return err
			}
			return nil
		}); err != nil {
			return nil, err
		}
		log.Printf("Installed system %q\n", req.SystemId)
		s.scheduler.Reset(ctx, req.SystemId)
	} else {
		var keepGoing bool
		if err := s.pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
			querier := db.New(tx)
			var err error
			keepGoing, err = beginSystemInstall(ctx, querier, req.SystemId, systemConfig.Name, req.InstallOnly)
			return err
		}); err != nil {
			return nil, err
		}
		if keepGoing {
			go func() {
				// TODO: can we wire through the context on the server?
				ctx := context.Background()
				err := s.pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
					return performSystemInstall(ctx, db.New(tx), req.SystemId, systemConfig)
				})
				if err := s.pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
					return finishSystemInstall(ctx, db.New(tx), req.SystemId, err)
				}); err != nil {
					log.Printf("Failed to finish installing system %q: %s", req.SystemId, err)
					return
				}
				log.Printf("Installed system %q\n", req.SystemId)
				s.scheduler.Reset(ctx, req.SystemId)
			}()
		}
	}
	return &api.InstallOrUpdateSystemReply{}, nil
}

func beginSystemInstall(ctx context.Context, querier db.Querier, systemID string, systemName string, installOnly bool) (bool, error) {
	system, err := querier.GetSystem(ctx, systemID)
	if err == pgx.ErrNoRows {
		if _, err = querier.InsertSystem(ctx, db.InsertSystemParams{
			ID:     systemID,
			Name:   systemName,
			Status: constants.Installing,
		}); err != nil {
			return false, err
		}
	} else if err != nil {
		return false, err
	} else {
		if installOnly && system.Status == constants.Active {
			return false, nil
		}
		if err = querier.UpdateSystemStatus(ctx, db.UpdateSystemStatusParams{
			Pk:     system.Pk,
			Status: constants.Updating,
		}); err != nil {
			return false, err
		}
	}
	return true, nil
}

func performSystemInstall(ctx context.Context, querier db.Querier, systemID string, config *config.SystemConfig) error {
	system, err := querier.GetSystem(ctx, systemID)
	if err != nil {
		return err
	}
	if err := querier.UpdateSystem(ctx, db.UpdateSystemParams{
		Pk:   system.Pk,
		Name: config.Name,
	}); err != nil {
		return err
	}

	// Service maps need to be updated before feeds. This is because updating a feed config may
	// trigger a feed update (if required_for_install=true) which may require the updated service
	// map config. This is tested in the end-to-end tests.
	if err := servicemaps.UpdateConfig(ctx, querier, system.Pk, config.ServiceMaps); err != nil {
		return err
	}

	feeds, err := querier.ListFeedsInSystem(ctx, system.Pk)
	if err != nil {
		return err
	}
	feedIDToPk := map[string]int64{}
	for _, feed := range feeds {
		feedIDToPk[feed.ID] = feed.Pk
	}

	for _, newFeed := range config.Feeds {
		if pk, ok := feedIDToPk[newFeed.ID]; ok {
			if err := querier.UpdateFeed(ctx, db.UpdateFeedParams{
				FeedPk:                pk,
				PeriodicUpdateEnabled: newFeed.PeriodicUpdateEnabled,
				PeriodicUpdatePeriod:  convertNullDuration(newFeed.PeriodicUpdatePeriod),
				Config:                string(newFeed.MarshalToJSON()),
			}); err != nil {
				return err
			}
			delete(feedIDToPk, newFeed.ID)
		} else {
			// TODO: is there a lint to detect not handling the error here?
			querier.InsertFeed(ctx, db.InsertFeedParams{
				ID:                    newFeed.ID,
				SystemPk:              system.Pk,
				PeriodicUpdateEnabled: newFeed.PeriodicUpdateEnabled,
				PeriodicUpdatePeriod:  convertNullDuration(newFeed.PeriodicUpdatePeriod),
				Config:                string(newFeed.MarshalToJSON()),
			})
		}
		if newFeed.RequiredForInstall {
			if err := update.CreateAndRunInExistingTx(ctx, querier, systemID, newFeed.ID); err != nil {
				return err
			}
		}
	}
	for _, pk := range feedIDToPk {
		querier.DeleteFeed(ctx, pk)
	}
	return nil
}

func finishSystemInstall(ctx context.Context, querier db.Querier, systemID string, installErr error) error {
	system, err := querier.GetSystem(ctx, systemID)
	if err != nil {
		return err
	}
	var newStatus string
	if installErr != nil {
		if system.Status == constants.Installing {
			newStatus = constants.InstallFailed
		} else {
			newStatus = constants.UpdateFailed
		}
	} else {
		newStatus = constants.Active
	}
	if err := querier.UpdateSystemStatus(ctx, db.UpdateSystemStatusParams{
		Pk:     system.Pk,
		Status: newStatus,
	}); err != nil {
		return err
	}
	return installErr
}

func (s *Service) DeleteSystem(ctx context.Context, req *api.DeleteSystemRequest) (*api.DeleteSystemReply, error) {
	log.Printf("Recieved delete request for system %q", req.SystemId)
	if err := s.pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		system, err := querier.GetSystem(ctx, req.SystemId)
		if err != nil {
			if err == pgx.ErrNoRows {
				err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
			}
			return err
		}
		return querier.DeleteSystem(ctx, system.Pk)
	}); err != nil {
		return nil, err
	}
	log.Printf("Deleted system %q", req.SystemId)
	s.scheduler.Reset(ctx, req.SystemId)
	return &api.DeleteSystemReply{}, nil
}

func getRawSystemConfigFromURL(url string) ([]byte, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to read transit system config from URL %q: %w", url, err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read transit system config from URL %q: %w", url, err)
	}
	return body, nil
}

func parseSystemConfigYaml(rawContent []byte, isTemplate bool, templateArgs map[string]string) (*config.SystemConfig, error) {
	if !isTemplate {
		return config.UnmarshalFromYaml(rawContent)
	}
	type Input struct {
		Args map[string]string
	}
	input := Input{Args: templateArgs}
	tmpl, err := template.New("transiter-system-config").Parse(string(rawContent))
	if err != nil {
		return nil, fmt.Errorf("failed to parse input as a Go text template: %w", err)
	}
	var b bytes.Buffer
	err = tmpl.Execute(&b, input)
	if err != nil {
		return nil, fmt.Errorf("failed to parse input as a Go text template: %w", err)
	}
	return config.UnmarshalFromYaml(b.Bytes())
}

// TODO: move to convert/converters
func convertNullDuration(d *time.Duration) sql.NullInt32 {
	if d == nil {
		return sql.NullInt32{}
	}
	return sql.NullInt32{
		Valid: true,
		Int32: int32(d.Milliseconds()),
	}
}
