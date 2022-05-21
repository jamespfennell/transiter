package main

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/jamespfennell/transiter/internal/argsflag"
	"github.com/jamespfennell/transiter/internal/client"
	"github.com/jamespfennell/transiter/internal/server"
	"github.com/urfave/cli/v2"
)

func main() {
	argsMap := map[string]string{}
	app := &cli.App{
		Name:  "Transiter",
		Usage: "web service for transit data",
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:    "addr",
				Aliases: []string{"a"},
				Usage:   "address of the Transiter server's gRPC admin API",
				Value:   "localhost:8083",
			},
		},
		Commands: []*cli.Command{
			{
				Name:  "delete",
				Usage: "delete a transit system",
				Action: func(c *cli.Context) error {
					if c.Args().Len() == 0 {
						return fmt.Errorf("must provide the ID of the system to delete")
					}
					return clientAction(func(ctx context.Context, client *client.Client) error {
						return client.DeleteSystem(ctx, c.Args().Get(0))
					})(c)
				},
			},
			{
				Name:  "install",
				Usage: "install a transit system",
				Flags: []cli.Flag{
					&cli.BoolFlag{
						Name:    "file",
						Aliases: []string{"f"},
						Usage:   "interpret the second argument as a local file path",
						Value:   false,
					},
					&cli.BoolFlag{
						Name:  "template",
						Usage: "indicates that the input file is a Go template",
						Value: false,
					},
					&cli.BoolFlag{
						Name:    "update",
						Aliases: []string{"u"},
						Usage:   "if the system is already installed, update it with the provided config",
						Value:   false,
					},
					argsflag.NewCliFlag("arg", "", argsMap),
				},
				Action: func(c *cli.Context) error {
					if c.Args().Len() == 0 {
						return fmt.Errorf("must provide the ID of the system to delete")
					}
					// TODO: pass the file name using --file and url using --url
					if c.Args().Len() == 1 {
						return fmt.Errorf("must provide a URL or file path for the transit system Yaml config")
					}
					args := client.InstallSystemArgs{
						SystemID:     c.Args().Get(0),
						ConfigPath:   c.Args().Get(1),
						IsFile:       c.Bool("file"),
						AllowUpdate:  c.Bool("update"),
						IsTemplate:   c.Bool("template") || c.IsSet("arg"),
						TemplateArgs: c.Value("arg").(map[string]string),
					}
					return clientAction(func(ctx context.Context, client *client.Client) error {
						return client.InstallSystem(ctx, args)
					})(c)
				},
			},
			{
				Name:  "list",
				Usage: "list all installed transit systems",
				Action: clientAction(func(ctx context.Context, client *client.Client) error {
					return client.ListSystems(ctx)
				}),
			},
			{
				Name:  "scheduler",
				Usage: "perform operations on the Transiter feed update scheduler",
				Subcommands: []*cli.Command{
					{
						Name:  "status",
						Usage: "list the active periodic feed update tasks",
						Action: clientAction(func(ctx context.Context, client *client.Client) error {
							return client.SchedulerStatus(ctx)
						}),
					},
					{
						Name:  "reset",
						Usage: "reset all of the periodic feed update tasks",
						Action: clientAction(func(ctx context.Context, client *client.Client) error {
							return client.ResetScheduler(ctx)
						}),
					},
				},
			},
			{
				Name:  "server",
				Usage: "run a Transiter server",
				Action: func(c *cli.Context) error {
					return server.Run(server.RunArgs{
						PublicHTTPAddr:   c.String("public-http-addr"),
						PostgresAddress:  c.String("postgres-address"),
						PostgresUser:     c.String("postgres-user"),
						PostgresPassword: c.String("postgres-password"),
						PostgresDatabase: c.String("postgres-database"),
						MaxConnections:   50,
					})
				},
				Flags: []cli.Flag{
					&cli.StringFlag{
						Name:  "public-http-addr",
						Usage: "Address for the public HTTP server to listen on",
						Value: "localhost:8080",
					},
					&cli.StringFlag{
						Name:  "postgres-address",
						Usage: "Postgres address",
						Value: "localhost:5432",
					},
					&cli.StringFlag{
						Name:  "postgres-user",
						Usage: "Postgres user",
						Value: "transiter",
					},
					&cli.StringFlag{
						Name:  "postgres-password",
						Usage: "Postgres password",
						Value: "transiter",
					},
					&cli.StringFlag{
						Name:  "postgres-database",
						Usage: "Postgres database",
						Value: "transiter",
					},
				},
			},
			{
				Name:  "feed",
				Usage: "perform operations on a data feed",
				Subcommands: []*cli.Command{
					{
						Name:  "update",
						Usage: "perform a feed update",
						Action: func(c *cli.Context) error {
							if c.Args().Len() == 0 {
								return fmt.Errorf("must provide the ID of the feed to update in the form <system_id>/<feed_id>")
							}
							feedAndSystemIds := strings.SplitAfterN(c.Args().Get(0), "/", 2)
							if len(feedAndSystemIds) != 2 {
								return fmt.Errorf("must provide the ID of the feed to update in the form <system_id>/<feed_id>")
							}
							systemID := strings.TrimSuffix(feedAndSystemIds[0], "/")
							feedID := feedAndSystemIds[1]
							if systemID == "" || feedID == "" {
								return fmt.Errorf("must provide the ID of the feed to update in the form <system_id>/<feed_id>")
							}
							return clientAction(func(ctx context.Context, client *client.Client) error {
								return client.UpdateFeed(ctx, systemID, feedID)
							})(c)
						},
					},
					// TODO: pause, unpause, status, etc
				},
			},
		},
	}
	if err := app.Run(os.Args); err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
}

func clientAction(f func(ctx context.Context, client *client.Client) error) func(c *cli.Context) error {
	return func(c *cli.Context) error {
		client, err := client.New(c.String("addr"))
		if err != nil {
			return err
		}
		defer client.Close()
		// TODO: parse the error to remove RPC references
		// For example when a yaml config url provided to install is incorrect
		return f(context.Background(), client)
	}
}
