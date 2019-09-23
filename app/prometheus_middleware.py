import time

import prometheus_client
from flask import request, Response
from prometheus_client import CollectorRegistry
from prometheus_client import Counter, Histogram

# collector registry to collect metrics
registry = CollectorRegistry()

# metric which counts requests, divided by url, HTTP method, HTTP status
REQUEST_COUNT = Counter('request_count',
                        'App Request Count',
                        ['app_name', 'method', 'endpoint', 'http_status'],
                        registry=registry
                        )

# metric which calculates latency of the requests
REQUEST_LATENCY = Histogram('request_latency_seconds',
                            'Request latency',
                            ['app_name', 'endpoint'],
                            registry=registry,
                            )

APP_LABEL = 'nat_inst_test_app'


def start_timer():
    """Sets start_time attribute of the flask's global variable 'request' with the current time."""
    request.start_time = time.time()


def stop_timer(response):
    """
    Calculates the actual time of request execution and adds this information as an observation for REQUEST_LATENCY
    metric.
    :param response: The response object that is used by default in Flask
    :return: the same object from params without any changes (just to support the interface)
    """
    resp_time = time.time() - request.start_time
    REQUEST_LATENCY.labels(APP_LABEL, request.path).observe(resp_time)
    return response


def record_request_data(response):
    """
    Increments counter for request with specific HTTP method, url and status code.
    :param response: The response object that is used by default in Flask
    :return: the same object from params without any changes (just to support the interface)
    """
    REQUEST_COUNT.labels(APP_LABEL, request.method, request.path, response.status_code).inc()
    return response


def setup_metrics(app):
    """
    The actual middleware function. Uses Flask's app before_request and after_request methods to collect defined metrics
    for each request.
    Also registers new endpoint for exposing collected metrics to Prometheus.

    :param app: Flask app instance
    :return: None
    """
    app.before_request(start_timer)

    app.after_request(record_request_data)
    app.after_request(stop_timer)

    @app.route('/metrics')
    def metrics():
        """ Endpoint for exposing latest metrics to Prometheus"""
        return Response(prometheus_client.generate_latest(registry), mimetype='text/plain; charset=utf-8')
