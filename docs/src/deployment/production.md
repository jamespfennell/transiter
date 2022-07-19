# Production advice

This page contains some advice on running Transiter in production.

The Transiter web service is a Python WSGI app (specifically built using Flask).
There is one core rule for such apps: don't expose them directly to
    the outside world.
Put them behind a reverse proxy like Nginx.
This will stop your deployment from being vulnerable to basic attacks.

Moreover, the [Transiter permissions system](permissions.md) is built around the assumption that 
    Transter is behind a reverse proxy.
So, without using one, there is no way to stop arbitrary users from, for example,
    deleting all the transit systems you have installed.


For configuring the reverse proxy, Transiter doesn't require much special attention 
with the two exceptions below.
Run Transiter listening on some port on the machine, and then proxy traffic directly to that port.
There are just two things to keep in mind:

- Permissions: as described in [the permissions page](permissions.md), 
    a HTTP header must be set to restrict access to certain endpoints.
- API discovery: as you'll have noticed, Transiter has a system for API discovery
    in which URLs are given in the JSON response.
    For this system to work the base URL needs to be known, and in a reverse proxy context this
    is often lost.
    Therefore, when proxying set the `X-Transiter-Host` HTTP header to be the ultimate base URL that
    the user sees.
    Transiter will use this to build the correct URL.
    
A full Nginx config implementing these ideas looks like this:

```text
server {

  server_name www.example.com;
  
  # This is not strictly necessary, but is a nice-to-have.
  location /transiter/v0.4/admin {
    return 403;
  }

  location /transiter/v0.4/ {
    proxy_set_header X-Real-IP  $remote_addr;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Transiter-Host "https://www.example.com/transiter/v0.4";
    proxy_set_header X-Transiter-PermissionsLevel "ADMIN_READ";
    proxy_set_header Host $host;
    proxy_pass http://127.0.0.1:8004/;
  }
}
```
