# Documentation

Transiter can be configured to serve the documentation 
on the `/docs` path.
This requires that the documentation has been built into static
files using `mkdocs`; Transiter then serves files directly from 
the documentation build directory.

## Security and performance notes

Please be aware that there is an inherent security concern here.
If the documentation is misconfigured, Transiter may serve
files from a random directory on the host machine and may thus leak 
data and files on the machine. 
To address this concern,

1. The documentation is disabled by default. A person setting up a Transiter instance
    has to explicitly enable it by setting the environment variable
    `TRANSITER_DOCUMENTATION_ENABLED` to be true.
    If the documentation is disabled any path on `/docs` returns a
    `404 NOT FOUND` response.
    
2. When serving documentation, Transiter will make an effort to ensure that the
    configuration is correct and that it is really serving the documentation
    and not some other directory. 
    To do this, Transiter embeds a 96 character hex string in each documentation page
    and before serving files verifies that the hex string is in the `index.html`
    file at the root of the directory.
    This security mechanism addresses accidental mistakes.
    If the security check fails, a `503 SERVICE UNAVAILABLE` response is sent.
    
In addition to the security concern, there is also a performance concern.
The files are served using Python's Flask and Werkzeug libraries; this 
is a highly non-performant way to serve static content.
In addition, the security check described above entails an additional fixed computational
cost for serving each file.
For these performance reasons, consider not enabling the documentation
in production if malicious users could access it and use it as the basis
for a DoS attack.


## Setting up the documentation

First, to enable the documentation set the environment 
variable
    `TRANSITER_DOCUMENTATION_ENABLED` to be true.
    
Next, you need to compile the documentation.
In the Python environment you're working in, ensure 
the Transiter developer requirements have been installed;
in the root of the Github repo, run
```sh
pip install -r dev-requirements.txt
```
Then `cd` into the `docs` directory and run
```sh
mkdocs build
```
This will result in the documentation static files being built
and placed in the `site` subdirectory.

Finally, configure the 
`TRANSITER_DOCUMENTATION_ROOT` environment variable.
This should point to the `site` subdirectory. 
This can be either:

1. An absolute path.

2. A relative path, relative to the location of the Flask application.

If you're launching the Flask app based on the checked out Github
repo, it is located in `transiter/http` and hence the 
environment variable should be set
to `../../docs/site`. (This is, in fact, the default.)

Verify it's working by visiting the `/docs` path.
If it's not working, consult the console output which will detail
exactly what's happening.

## Documentation in the Docker image

The Docker image contains the built HTML documentation in the directory
`/transiter-docs`.
The internal documentation is disabled by default.