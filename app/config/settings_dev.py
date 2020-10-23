"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from .settings_prod import *  # pylint: disable=wildcard-import, unused-wildcard-import

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': 'middleware.debug_toolbar.check_toolbar_env'}

# use the default staticfiles mechanism
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
