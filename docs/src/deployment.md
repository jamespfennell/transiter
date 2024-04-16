# Deploying Transiter

Transiter is simply a Go binary that requires a running Postgres instance.
There are thus many ways to deploy Transiter.

We recommend deploying Transiter using the Transiter Docker image.
This Docker image is built on every push to mainline and
  [stored in Docker Hub](https://hub.docker.com/r/jamespfennell/transiter).
The latest build always has tag `jamespfennell/transiter:latest`.
Each build on mainline gets its own specific tag too,
  in case you want to pin to a specific version.
The tags have one of two forms:

- For _releases_ of version vA.B.C, the tag is `jamespfennell/transiter:vA.B.C`
- For non-release builds on mainline of version vA.B.C, the tag is `jamespfennell/transiter:vA.B.C-beta.buildN`,
    where N is a GitHub build number.
    The easiest way to find a valid tag is to
    [browse the tags in Docker Hub](https://hub.docker.com/r/jamespfennell/transiter/tages).

This is an example Docker compose configuration
  which runs the Transiter Docker image alongside a Postgres Docker image:

```
version: '3.5'

services:

  transiter:
    image: jamespfennell/transiter:1.0.0-beta.build12
    ports:
      - "127.0.0.1:8080:8080"
      - "127.0.0.1:8081:8081"
      - "127.0.0.1:8082:8082"
      - "127.0.0.1:8083:8083"
    restart: always
    command:
      - server
      - --log-level
      - info
      - --postgres-connection-string
      - "postgres://transiter:transiter@postgres:5432/transiter"

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_USER=transiter
      - POSTGRES_PASSWORD=transiter
      - POSTGRES_DB=transiter
    volumes:
      # Persist the Postgres data outside the container to that it persists across restarts.
      - "${HOME}/transiter-data:/var/lib/postgresql/data"
    restart: always
```

The Postgres you use doesn't need to be on the same machine.
You can even used a managed Postgres service like Google's CloudSQL.

## Reverse proxy

Generally Transiter should be run behind a reverse proxy like Caddy or Nginx,
  for the usual reverse proxy reasons.
This is a sample Caddyfile configuration for Caddy:

```
demo.transiter.dev {
    encode gzip
    reverse_proxy 127.0.0.1:8080 {
        header_up X-Transiter-Host "https://demo.transiter.dev"
    }
}
```

In this case requests to `demo.transiter.dev` are reverse proxied to `localhost:8080`.
This is where the Transiter public HTTP API is listening if you used the Docker compose
  configuration above.

## (Optional) Setting the Transiter host


The reverse proxy configuration above contains a `X-Transiter-Host` header instruction.
This tells Caddy that when a HTTP request is forwarded to Transiter, the `X-Transiter-Host`
  header should be added with value `https://demo.transiter.dev`.

The point of this optional header is to support Transiter's version of "HATEOAS".
When this header is set, every resource that is returned will have the full URL of the resource in the response.
For example, when [listing systems on the demo site](https://demo.transiter.dev/systems),
  the NYC subway resource contains the exact URL `https://demo.transiter.dev/systems/us-ny-subway`
  for the resource.
In general Transiter knows nothing about the base URL, so the `X-Transiter-Host` provides it.
If the header is missing, Transiter simply skips returning URLs.


## Admin APIs

In general you will only want to make the public HTTP API (default port 8080)
  and/or public gRPC API (default port 8081) available to the internet.
The admin APIs (on ports 8082 and 8083) should be hidden so that internet users
  can't e.g. delete all your transit systems.
With the Docker compose configuration above,
  these APIs are still available locally on the machine so you can still administer the Transiter instance
  by SSHing into the machine.

Sometimes you may want to administer a remote Transiter instance from your personal computer.
You can use SSH port forwarding to do this.
If your admin gRPC API is listing on port 8083 (as above), run the following command on your personal computer:

```
ssh -N -L8083:localhost:8083 $HOST_RUNNING_TRANSITER
```

Now port 8083 on your personal computer is linked to the Transiter admin API on the remote machine.
This means you can run something like:

```
transiter list
```

on your personal machine and it will work.
You can also install/delete transit systems this way, and so on.


## Monitoring

After deploying Transiter you [may be interested in monitoring it](monitoring.md).
