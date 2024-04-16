# Transiter documentation

To build the documentation run `just docs`.
This puts the documentation in the directory `$REPO_ROOT/docs/gen`.
Python is used to build the documentation.
As usual, it is best to run the command inside a Python virtual environment.

The documentation is built in the Transiter Docker image and placed
    into the `/usr/share/docs/transiter` directory.
The Docker image also includes the Caddy file server program.
Thus the documentation can be served from the Docker image on port 9000 using this Docker command:

```
docker run --entrypoint caddy -p 9000:80 jamespfennell/transiter:latest file-server --root /usr/share/doc/transiter
```

Or, this Docker compose config:

```
version: '3.5'
services:
    transiter-docs:
        image: jamespfennell/transiter:latest
        entrypoint: caddy
        command: file-server --root /usr/share/doc/transiter
        ports:
            - "9000:80"
```
