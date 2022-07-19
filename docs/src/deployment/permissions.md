# Permissions

Many endpoints exposed by Transiter, such as the install and delete systems endpoints,
    are subject to permissions restrictions
    so that arbitrary users cannot alter the Transiter instance.
The permissions system is very basic and assumes that Transiter is running behind a reverse proxy like Nginx.


Every endpoint has a required permissions level.
In order of increasing restriction, there are three permissions levels:

1. `USER_READ` - the default, any user can access this endpoint.
1. `ADMIN_READ` - any user with `ADMIN_READ` or `ALL` permissions can access this endpoint.
1. `ALL` - a user must have `ALL` permission to access this endpoint.

An endpoint having a required permissions level means that the user of the endpoint
must have at that level or higher of permissions.
    
The permissions level of a user is determined by a specific HTTP header
    `X-Transiter-PermissionsLevel`
    that the user sends in the HTTP request.
If not provided, the permission level defaults to `ALL`.


As currently described, any user hitting Transiter directly has access to all endpoints.
The key to the system is putting Transiter behind a reverse proxy like Nginx, and then
    in forwarding the request to Transiter adding in the desired permissions header.
If the Transiter webservice is listening on port 8000, this Nginx config
    proxies to the webservice and adds the `USER_READ` permissions:

```text
  location / {
    proxy_set_header X-Real-IP  $remote_addr;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Transiter-PermissionsLevel "USER_READ";
    proxy_set_header Host $host;
    proxy_pass http://127.0.0.1:8000/;
  }
```