from flask import Flask


def create_app(config_object):
    """
    Initialize the core application with specified config object.
    Then adds a blueprint with prefix '/api/v1/'.
    Then adds Redis client
    Then adds Prometheus middleware
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # add blueprint
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1/')

    # add redis client
    from app.redis_init import redis_client
    redis_client.init_app(app)

    # add prometheus middleware
    from app.prometheus_middleware import setup_metrics
    setup_metrics(app)

    return app


# create app with dev-config
app = create_app("app.config.DevelopmentConfig")

if __name__ == "__main__":
    app.run()
