import os
from django.test.utils import get_runner
import django
from django.conf import settings


def run_django_app_tests(settings_path, test_modules):
    """ Runs django unittests without using manage.py. 
    It is useful when tests are run with python2.7 setup.py test

    :param settings_path: dotted path to test settings module
    :param test_modules: list of test modules to run
    :returns: boolean representing if tests have finished without errors
    """
    os.environ["DJANGO_SETTINGS_MODULE"]=settings_path    
    django.setup()
    test_runner_cls = get_runner(settings)
    failures = test_runner_cls().run_tests(test_modules, verbosity=1, interactive=True)
    is_passed=not bool(failures)
    return is_passed
