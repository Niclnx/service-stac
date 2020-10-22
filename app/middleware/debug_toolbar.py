import os


def check_toolbar_env(request):
    """ callback to check whether debug toolbar should be shown or not

    for details see
    https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config  # pylint: disable=line-too-long
    """
    print(os.environ.get('APP_ENV'))
    if os.environ.get('APP_ENV', 'prod') in ['local', 'dev']:
        print('blublu')
        return True

    return False
