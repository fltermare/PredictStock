import os
import datetime

basedir = os.path.abspath(os.path.dirname(__file__))


# def create_sqlite_uri(db_name):
#     return "sqlite:///" + os.path.join(basedir, db_name)


class BaseConfig:
    SECRET_KEY = 'secret123'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=14)


class DevelopmentConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@db:5432/db"


class LocalTestConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/db"

# class TestingConfig(BaseConfig):
#     TESTING = True
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SQLALCHEMY_DATABASE_URI = create_sqlite_uri("test.db")


config = {
    'development': DevelopmentConfig,
    'localtest': LocalTestConfig,
    # 'testing': TestingConfig,
}