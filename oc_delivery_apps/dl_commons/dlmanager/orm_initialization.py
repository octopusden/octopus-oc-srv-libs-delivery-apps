#! /usr/bin/python2.7
from cdt.connections import ORMConfigurator


used_apps=["dlmanager",
           "checksums", # this and following apps should be moved to checksums.orm_initialization
           "django.contrib.auth", # User model
           "django.contrib.contenttypes", # referenced from User
]


def configure_dlmanager_orm(conn_mgr, **additional_settings):
    """ Shortcut for calling ORMConfigurator.configure_django_orm with proper params """
    ORMConfigurator.configure_django_orm(conn_mgr, INSTALLED_APPS=used_apps,
					 **additional_settings)
