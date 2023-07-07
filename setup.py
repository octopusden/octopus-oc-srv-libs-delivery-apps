#!/usr/bin/env python3
from setuptools import setup
import glob
import os

__version = "11.3.0"

spec = {
    "name": "oc-delivery-apps",
    "version": __version, 
    "description": "Models and controllers for dlcontents application",
    "long_description": "",
    "long_description_content_type": "text/plain",
    "license": "LGPLv2",
    "packages": [
        "oc_delivery_apps",
        "oc_delivery_apps.checksums",
        "oc_delivery_apps.checksums.migrations",
        "oc_delivery_apps.dlcontents",
        "oc_delivery_apps.dlcontents.migrations",
        "oc_delivery_apps.dlmanager",
        "oc_delivery_apps.dlmanager.migrations",
        "oc_delivery_apps.dlmanager.management",
        "oc_delivery_apps.dlmanager.management.commands",
    ],
    "install_requires": [
        "fs",
        "oc-sql-helpers >= 1.0.0",
        "oc-cdtapi",
        "python-magic",
        "oc-orm-initializator",
        "sqlparse",
        "configobj",
        "pytz"
    ],
    "python_requires": ">=3.6"
}

setup(**spec)
