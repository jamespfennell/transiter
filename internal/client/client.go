package client

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/jamespfennell/transiter/internal/client/table"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"google.golang.org/grpc"
)

type Client struct {
	conn         *grpc.ClientConn
	publicClient api.PublicClient
	adminClient  api.TransiterAdminClient
}

func New(addr string) (*Client, error) {
	var err error
	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("fail to dial: %v", err)
	}
	return &Client{
		conn:         conn,
		publicClient: api.NewPublicClient(conn),
		adminClient:  api.NewTransiterAdminClient(conn),
	}, nil
}

func (c *Client) Close() error {
	return c.conn.Close()
}

func (c *Client) DeleteSystem(ctx context.Context, systemId string) error {
	req := api.DeleteSystemRequest{SystemId: systemId}
	_, err := c.adminClient.DeleteSystem(ctx, &req)
	return err
}

type InstallSystemArgs struct {
	SystemId     string
	ConfigPath   string
	IsFile       bool
	AllowUpdate  bool
	IsTemplate   bool
	TemplateArgs map[string]string
}

func (c *Client) InstallSystem(ctx context.Context, args InstallSystemArgs) error {
	yamlConfig := &api.YamlConfig{
		IsTemplate:   args.IsTemplate,
		TemplateArgs: args.TemplateArgs,
	}
	if args.IsFile {
		yaml, err := os.ReadFile(args.ConfigPath)
		if err != nil {
			return err
		}
		yamlConfig.Source = &api.YamlConfig_Content{
			Content: string(yaml),
		}
	} else {
		yamlConfig.Source = &api.YamlConfig_Url{
			Url: args.ConfigPath,
		}
	}
	req := api.InstallOrUpdateSystemRequest{
		SystemId:    args.SystemId,
		InstallOnly: !args.AllowUpdate,
		Config: &api.InstallOrUpdateSystemRequest_YamlConfig{
			YamlConfig: yamlConfig,
		},
		Synchronous: false,
	}
	_, err := c.adminClient.InstallOrUpdateSystem(ctx, &req)
	if err != nil {
		return err
	}

	for {
		system, err := c.publicClient.GetSystem(ctx, &api.GetSystemRequest{SystemId: args.SystemId})
		if err != nil {
			return fmt.Errorf("failed to poll system status: %w", err)
		}
		switch system.Status {
		case api.System_ACTIVE:
			return nil
		case api.System_INSTALL_FAILED, api.System_UPDATE_FAILED:
			return fmt.Errorf("failed to install/update system")
		default:
			time.Sleep(100 * time.Millisecond)
		}
	}
}

func (c *Client) UpdateFeed(ctx context.Context, systemId, feedId string) error {
	_, err := c.adminClient.UpdateFeed(ctx, &api.UpdateFeedRequest{
		SystemId: systemId,
		FeedId:   feedId,
	})
	return err
}

func (c *Client) ListSystems(ctx context.Context) error {
	var req api.ListSystemsRequest
	rep, err := c.publicClient.ListSystems(ctx, &req)
	if err != nil {
		return err
	}
	if len(rep.Systems) == 0 {
		fmt.Println("No transit systems installed.")
		return nil
	}
	t := table.New()
	t.AddRow("ID", "Name")
	t.AddSeperator()
	for _, system := range rep.Systems {
		t.AddRow(system.Id, system.Name)
	}
	fmt.Printf("%s", t.Render())
	return nil
}

func (c *Client) SchedulerStatus(ctx context.Context) error {
	var req api.GetSchedulerStatusRequest
	reply, err := c.adminClient.GetSchedulerStatus(ctx, &req)
	if err != nil {
		return err
	}
	t := table.New()
	t.AddRow("System ID", "Feed ID", "Period", "Last", "Last", "Currently")
	t.AddRow("", "", "", "finished", "succesful", "running")
	t.AddRow("", "", "", "update", "update", "")
	t.AddSeperator()
	for _, feed := range reply.Feeds {
		t.AddRow(
			feed.SystemId,
			feed.FeedId,
			(time.Millisecond * time.Duration(feed.Period)).String(),
			convertTime(feed.LastFinishedUpdate),
			convertTime(feed.LastSuccessfulUpdate),
			fmt.Sprintf("%t", feed.CurrentlyRunning))
	}
	fmt.Printf("%s", t.Render())
	return nil
}

func (c *Client) ResetScheduler(ctx context.Context) error {
	var req api.ResetSchedulerRequest
	_, err := c.adminClient.ResetScheduler(ctx, &req)
	return err
}

func convertTime(t int64) string {
	if t == 0 {
		return "(none)"
	}
	return fmt.Sprintf("%s ago", time.Now().Round(time.Second).Sub(time.Unix(t, 0)))
}
