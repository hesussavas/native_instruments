#Solution for test assignment from Native Instruments

## Assignment
You are to design an API for a key-value store application, complete with tests, local deployment 
environment and documentation

The application can be interfaced with via HTTP, its endpoints providing the following functionalities:

+ get a value (GET /keys/{id})
+ get all keys and values (GET /keys)
+ support wildcard keys when getting all values (GET /keys?filter=wo$d)

+ check if a value exists (HEAD /keys/{id})

+ set a value (PUT /keys)
+ set an expiry time when adding a value (PUT /keys?expire_in=60)

+ delete a value (DELETE /keys/{id})
+ delete all values (DELETE /keys)

- The application will log any output to stdout
- The application will use HTTP status codes to communicate the success or failure of an operation
- The data stored will be persisted so that restarts of the application don’t clear it
- The application should also provide an integration with a monitoring solution (for example Prometheus).
- Please instrument your application so that the metrics can be viewed.
- The solution should be provided as a single archive, containing a git repository and a Docker Compose file 
to start the application

*Criteria*
- the solution works as expected, the tests you provide pass
- you are free to pick a language to implement in, but we have a strong preference for Python
- the code style makes it easily maintainable, extendable and is according to the general best practices 
of the chosen platform
- appropriate use of logging and metrics
- documentation:
    - of the solution (is present and good enough to give an overview)
    - of the code (is present where needed and not where obvious)
    - includes any known limitations or restrictions of the solution
    - mentions the platform tested on

*Remarks:*
- don’t spend time optimising, try to focus on solving the problem
- if you know that optimisations could be done, feel free to list them in a README
- provide a README file (markdown or plain text)

## Solution
This solution is a simple RESTish-API (couldn't be a pure REST app because of the seversal requirements 
in assignment) implemented with `Python 3.7` as a `Flask` application with `Redis` cache 
as a data persistence source.
When application is running, there is an endpoint at `/api/v1/keys/` which handles all the requests 
mentioned in assignment.
There is also another endpoint at `/metrics` which exposes Prometheus metrics.

## At  a glance
Roughly application is a wrapper around different Redis methods.
Redis was chosen, cause the purpose of the app is close to the Redis functionality.
Moreover, almost all functionality is covered by Redis own methods.
For example, 
- to get a value we use redis' [GET](https://redis.io/commands/get)
- to delete a value we use redis' [DELETE](https://redis.io/commands/delete)
- to delete all values we use redis' [FLUSHALL](https://redis.io/commands/flushall)
- to add new value we use redis' [SET](https://redis.io/commands/set)
- to add and expiration to the value we use redis' [EXPIRE](https://redis.io/commands/expire)
- to get all keys and values we use redis' [KEYS](https://redis.io/commands/keys) 
and [MGET](https://redis.io/commands/keys) in a row.

Redis also supports glob-style patterns for keys search - so, no need to implement it from the scratch - 
we need to just replace `$` with `?` in pattern.
And also redis built-in support for expiration of the keys.

## How to run
To satisfy the requirement for a Docker, there is a `Dockerfile` and `docker-compose.yml` files in the repo.

There is also a `Makefile`, which allows you run the application under Docker with less typing and need 
for remembering docker-compose commands.

So, use `make run_app` to run the application in development mode. This command will run the 
application at `http://0.0.0.0:5000/`

*(Under the hood it will call `docker-compose up web`)* 


Now you could try to reach the app with requests like this (all examples are for [httpie](https://httpie.org/)):

`http PUT 0.0.0.0:5000/api/v1/keys/ key=test value=42` (add new key)

`http 0.0.0.0:5000/api/v1/keys/` (get all keys)

`http DELETE 0.0.0.0:5000/api/v1/keys/test` (delete newly created key)


## Prometheus support
As was mentioned before, it's possible to get metrics exposed for Prometheus at:

`http 0.0.0.0:5000/metrics`

There are just 2 simple metrics collected: request count *(request_count)* and 
request's latency *(request_latency_seconds)*.

`request_count` - Counter, just counting requests aggregated by HTTP-method, url and status code

`request_latency_seconds` -  Histogram, which calculates execution time of the request.

All requests will have label `nat_inst_test_app`.

## Unittests
There are also unittests. 13 unittests for api functionality and 1 doctest for inner util function. All of them are 
assembled in a single suite and could be run inside a Docker container with a following command:
`make unittest`

*(Under the hood it will call `docker-compose up unittest`)* 

For the simplicity all Redis calls are mocked in unittests.


##Tested with
Tested under Docker Desktop for Mac v2.1.0.0, Docker engine: 19.03.1

## Possible improvements
- add pagination for get all keys and values method (will be helpful on a big amount of stored data)
- change `reqparse` library with `marshmallow` (`reqparse` is deprecated) for arguments parsing inside flask-restful app
- add swagger schema fro API (for readability)
- create separate config for production (now it's only for Development and Test)
- add more metrics to prometheus (if needed)
- more validity checks for input data in HTTP methods (only `expire_in` keyword is tested for 
validity (is numeric) now.)
- serve metrics from the other port (for security reasons. Now there is the same port for metrics and API)
- authentication (add at least basic-auth for the API. Now there is nothing - cause there were no requirement)
- configuration with environment variables (especially for production).