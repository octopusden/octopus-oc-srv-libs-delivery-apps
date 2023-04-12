#!/usr/bin/env python3
from setuptools import setup
import glob
import os

__version = "11.2.0.1"

spec = {
    'name': "oc-delivery-apps",
    'version': __version, 
    'description': 'Models and controllers for dlcontents application',
    'license': "LGPLv2",
    'packages': [
        'oc_delivery_apps',
        'oc_delivery_apps.checksums',
        'oc_delivery_apps.dlcontents'],
    'install_requires': [
        "oc-sql-helpers >= 0.16.0.0",
        "python-magic",
        "oc-orm-initializator",
        "sqlparse",
    ],
    "python_requires": ">=3.6"
}

setup(**spec)
