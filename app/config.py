class Config(object):
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True
    REDIS_URL = 'redis://:@redis/0'


class TestingConfig(Config):
    TESTING = True
