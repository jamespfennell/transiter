package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"strings"

	"github.com/jamespfennell/transiter/internal/argsflag"
	"github.com/jamespfennell/transiter/internal/client"
	"github.com/jamespfennell/transiter/internal/server"
	"github.com/jamespfennell/transiter/internal/version"
	"github.com/urfave/cli/v2"
	"golang.org/x/exp/slog"
)

func main() {
	argsMap := map[string]string{}
	app := &cli.App{
		Name:        "transiter",
		Usage:       "web service for transit data",
		Description: binaryDescription,
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
				Name:      "server",
				Usage:     "run a Transiter server",
				ArgsUsage: " ",
				Flags: []cli.Flag{
					addrFlag("public HTTP", "public-http", 8080),
					addrFlag("public gRPC", "public-grpc", 8081),
					addrFlag("admin HTTP", "admin-http", 8082),
					addrFlag("admin gRPC", "admin-grpc", 8083),
					&cli.StringFlag{
						Name:        "postgres-connection-string",
						Aliases:     []string{"p"},
						Usage:       "Postgres connection string",
						Value:       "postgres://transiter:transiter@localhost:5432/transiter",
						DefaultText: "postgres://transiter:transiter@localhost:5432/transiter",
					},
					&cli.Int64Flag{
						Name:  "postgres-max-connections",
						Usage: "Maximum size of the Postgres connection pool",
						Value: 50,
					},
					&cli.BoolFlag{
						Name:  "read-only",
						Usage: "Run the server in read only mode (no admin APIs, no scheduler, read-only database queries)",
						Value: false,
					},
					&cli.BoolFlag{
						Name:  "disable-scheduler",
						Usage: "Disable the feed update scheduler",
						Value: false,
					},
					&cli.BoolFlag{
						Name:  "enable-pprof",
						Usage: "Enable pprof debugging. When enabled, pprof dumps can be taken using the /debug/pprof endpoints of the admin HTTP API",
						Value: false,
					},
					&cli.BoolFlag{
						Name:  "disable-public-metrics",
						Usage: "Disable report Prometheus metric reporting on the public HTTP API's /metrics endpoint. Metrics are always reported in the admin HTTP API",
						Value: false,
					},
					&cli.Int64Flag{
						Name:  "max-entities-per-request",
						Usage: "Maximum number of stops, vehicles, and shapes that will be returned in a single request. Specifying a value <= 0 will disable the limit",
						Value: 100,
					},
					&cli.StringFlag{
						Name:        "log-level",
						Usage:       "The log level, either debug, info, warning or error. This can be changed after startup using the client's log-level command",
						Value:       "info",
						DefaultText: "info",
					},
				},
				Action: func(c *cli.Context) error {
					var logLevel slog.Level
					if err := logLevel.UnmarshalText([]byte(c.String("log-level"))); err != nil {
						return err
					}
					args := server.RunArgs{
						PublicHTTPAddr:        c.String("public-http-addr"),
						PublicGrpcAddr:        c.String("public-grpc-addr"),
						AdminHTTPAddr:         c.String("admin-http-addr"),
						AdminGrpcAddr:         c.String("admin-grpc-addr"),
						PostgresConnStr:       c.String("postgres-connection-string"),
						MaxConnections:        int32(c.Int64("postgres-max-connections")),
						DisableScheduler:      c.Bool("disable-scheduler"),
						DisablePublicMetrics:  c.Bool("disable-public-metrics"),
						ReadOnly:              c.Bool("read-only"),
						EnablePprof:           c.Bool("enable-pprof"),
						MaxEntitiesPerRequest: int32(c.Int64("max-entities-per-request")),
						LogLevel:              logLevel,
					}
					ctx, cancel := context.WithCancel(c.Context)
					defer cancel()

					interruptCh := make(chan os.Signal, 1)
					signal.Notify(interruptCh, os.Interrupt)
					defer signal.Stop(interruptCh)

					shutdownCh := make(chan error, 1)
					go func() {
						shutdownCh <- server.Run(ctx, args)
					}()

					var cancelled bool
					for {
						select {
						case <-interruptCh:
							if cancelled {
								return fmt.Errorf("forced an unclean shutdown after receiving second cancellation signal")
							}
							cancelled = true
							cancel()
						case err := <-shutdownCh:
							return err
						}
					}
				},
			},
			{},
			{
				Name:      "delete",
				Usage:     "delete a transit system",
				ArgsUsage: "<system_id>",
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
				Name:  "feed",
				Usage: "perform operations on a data feed",
				Subcommands: []*cli.Command{
					{
						Name:  "update",
						Usage: "perform a feed update",
						Flags: []cli.Flag{
							&cli.BoolFlag{
								Name:  "force",
								Usage: "Perform a full update even if the downloaded data is identical to the last time this feed was updated",
								Value: false,
							},
						},
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
								return client.UpdateFeed(ctx, systemID, feedID, c.Bool("force"))
							})(c)
						},
					},
					// TODO: pause, unpause, status, etc
				},
			},
			{
				Name:        "install",
				Usage:       "install a transit system",
				Description: installDescription,
				ArgsUsage:   "<system>",
				Flags: []cli.Flag{
					// id
					&cli.BoolFlag{
						Name:    "file",
						Aliases: []string{"f"},
						Usage:   "treat <system> as a file path and get the config by reading the file",
						Value:   false,
					},
					&cli.BoolFlag{
						Name:    "url",
						Aliases: []string{"u"},
						Usage:   "treat <system> as a URL and get the config by sending a GET request to the URL",
						Value:   false,
					},
					&cli.BoolFlag{
						Name:    "allow-update",
						Aliases: []string{"a"},
						Usage:   "if the system is already installed, update it with the provided config",
						Value:   false,
					},
					&cli.BoolFlag{
						Name:  "template",
						Usage: "indicates that the YAML config file is a Go template",
						Value: false,
					},
					argsflag.NewCliFlag("arg", "", argsMap),
					&cli.StringFlag{
						Name:        "id",
						Usage:       "system ID to install under",
						Value:       "",
						DefaultText: "inferred from <system>; e.g. my-system.yaml is installed under ID my-system",
					},
				},
				Action: func(c *cli.Context) error {
					if c.Args().Len() != 1 {
						return fmt.Errorf("exactly one argument <system> must be provided")
					}
					id := defaultSystemID(c.Args().Get(0))
					if idOverride := c.String("id"); idOverride != "" {
						id = idOverride
					}
					if c.Bool("file") && c.Bool("url") {
						return fmt.Errorf("both -f/--file and -u/--url cannot be provided as it's ambiguous whether <system> is a file or a URL")
					}
					configPathType := client.TransiterRepo
					if c.Bool("file") {
						configPathType = client.File
					}
					if c.Bool("url") {
						configPathType = client.URL
					}
					args := client.InstallSystemArgs{
						SystemID:       id,
						ConfigPath:     c.Args().Get(0),
						ConfigPathType: configPathType,
						AllowUpdate:    c.Bool("update"),
						IsTemplate:     c.Bool("template") || c.IsSet("arg"),
						TemplateArgs:   c.Value("arg").(map[string]string),
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
				Name:  "log-level",
				Usage: "get or set the log level on the server",
				Flags: []cli.Flag{
					&cli.StringFlag{
						Name:  "set",
						Usage: "The new value of the log level. If not specified, the current log level is just printed.",
						Value: "",
					},
				},
				Action: func(c *cli.Context) error {
					return clientAction(func(ctx context.Context, client *client.Client) error {
						if logLevel := c.String("set"); logLevel != "" {
							return client.SetLogLevel(ctx, logLevel)
						}
						return client.GetLogLevel(ctx)
					})(c)
				},
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
			{},
			{
				Name:  "version",
				Usage: "print the version of this binary, or a Transiter server",
				Flags: []cli.Flag{
					&cli.BoolFlag{
						Name:  "server",
						Usage: "Print the version of a Transiter server rather than this binary",
						Value: false,
					},
				},
				Action: func(ctx *cli.Context) error {
					if !ctx.Bool("server") {
						fmt.Println(version.Version())
						return nil
					}
					return clientAction(func(ctx context.Context, client *client.Client) error {
						version, err := client.Version(ctx)
						if err != nil {
							return err
						}
						fmt.Println(version)
						return nil
					})(ctx)
				},
			},
		},
	}
	if err := app.Run(os.Args); err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
}

const binaryDescription = `The Transiter program contains two types of command.

The ` + "`" + `transiter server` + "`" + ` command is used to start a Transiter server.
This is a long-running program that subscribes to transit data feeds
and provides APIs for querying transit data.

All of the other commands in this binary are client commands. These
perform operations on a running Transiter server, like installing a
or deleting a transit system.

Documentation: docs.transiter.dev.
GitHub repo: github.com/jamespfennell/transiter.`

const installDescription = `This command installs a transit system.

A YAML configuration file must be provided. If the system exists in
the Transiter
repository (see [1]) then the system can be installed simply by 
providing the ID of the system. This command will automatically pull
the config from the Transiter repo. For example, to install the Bay
Area BART:

    transiter install us-ca-bart

Alternatively, the system can be installed by providing a YAML
configuration from a local file:

	transiter install --file path/to/my-system.yaml

In this case the system will be given the ID my-system, but this can
be overridden by setting the --id flag. Similarly, the system can be
installed by providing the YAML configuration at a URL:

	transiter install --url example.com/my-system.yaml

As before, the system will be given the ID my-system and this can be
overridden.

By default, if the system with the provided ID already exists Transiter
will return an error. The motivation for this behavior is to avoid
unintentionally damaging an existing transit system. Passing the flag
--allow-update will instead the update the transit system with the
provided configuration.

Transit system configs can be plain YAML configs, or Go templates
that resolve to a YAML config. The flags --arg and --template are
used when the config is a Go template. See the documentation [2] for more
information on how templated configs work.

[1] https://github.com/jamespfennell/transiter/tree/master/systems
[2] https://docs.transiter.dev/systems
`

func defaultSystemID(system string) string {
	// remove the file extension
	if i := strings.LastIndex(system, "."); i >= 0 {
		system = system[:i]
	}
	// remove the directory
	if i := strings.LastIndexAny(system, `\/`); i >= 0 {
		system = system[i+1:]
	}
	return system
}

func addrFlag(api string, name string, defaultPort int) *cli.StringFlag {
	defaultValue := fmt.Sprintf("0.0.0.0:%d", defaultPort)
	return &cli.StringFlag{
		Name:        fmt.Sprintf("%s-addr", name),
		Usage:       fmt.Sprintf("Address for the %s service to listen on. Setting this flag to \"-\" disables the %s API", api, api),
		DefaultText: defaultValue,
		Value:       defaultValue,
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
