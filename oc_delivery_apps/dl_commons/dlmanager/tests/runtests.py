#! /usr/bin/python2.7

import sys
from django_tests.runner import run_django_app_tests


# currently dlmanager is treated as Django app, but after all it should become plain Python
def runtests(test_modules=[]):
    if not test_modules:
        test_modules=["dlmanager.test", ]
    return run_django_app_tests("dlmanager.test.test_settings",
                                test_modules)


def execute_test_suite():
    is_passed=runtests()
    sys.exit(0 if is_passed else 1)


if __name__ == '__main__':
    is_passed=runtests(sys.argv[1:])
    sys.exit(0 if is_passed else 1)
