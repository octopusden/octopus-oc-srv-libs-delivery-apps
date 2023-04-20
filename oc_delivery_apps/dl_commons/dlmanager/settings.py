""" These minimal settings are supposed to be used for migration creation """

import os
from cdt.connections.ConnectionManager import ConnectionManager


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, "static")


DEBUG = True
SECRET_KEY="key"


INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",

    "checksums",
    "dlmanager",
)


MIDDLEWARE_CLASSES = ()


conn_mgr=ConnectionManager()
db_url, db_user, db_password=conn_mgr.get_credentials_group("PSQL", ["URL", "USER",
                                                                               "PASSWORD"])
db_host, db_port, db_name, db_options=ConnectionManager.parse_conn_url(db_url)
DATABASES = {
        "default":{
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": db_name,
                "USER": db_user, 
                "PASSWORD": db_password,
                "HOST": db_host, 
                "PORT": db_port, 
                "OPTIONS":{ "options": "-c %s" % db_options  },
        },
}

