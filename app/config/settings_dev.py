"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
from distutils.util import strtobool

from .settings_prod import *  # pylint: disable=wildcard-import, unused-wildcard-import

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(strtobool(os.getenv('DEBUG', 'False')))
if DEBUG:
    print('WARNING - running in debug mode !')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

ALLOWED_HOSTS = ['*']

# django-extensions
# ------------------------------------------------------------------------------
if DEBUG:
    INSTALLED_APPS += ['django_extensions', 'debug_toolbar']

if DEBUG:
    MIDDLEWARE = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ] + MIDDLEWARE

# configuration for debug_toolbar
# see https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': 'middleware.debug.check_toolbar_env'}

# use the default staticfiles mechanism
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

if DEBUG:
    DEBUG_PROPAGATE_API_EXCEPTIONS = bool(
        strtobool(os.getenv('DEBUG_PROPAGATE_API_EXCEPTIONS', 'False'))
    )

SHELL_PLUS_POST_IMPORTS = ['from tests.data_factory import Factory']
