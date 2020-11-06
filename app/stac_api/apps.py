import logging

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions
from rest_framework import pagination
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class StacApiConfig(AppConfig):
    name = 'stac_api'


class CursorPagination(pagination.CursorPagination):
    ordering = 'id'
    page_size_query_param = 'limit'
    max_page_size = settings.REST_FRAMEWORK['PAGE_SIZE_LIMIT']

    def get_paginated_response(self, data):
        links = {}
        next_page = self.get_next_link()
        previous_page = self.get_previous_link()
        if next_page is not None:
            links.update({'rel': 'next', 'href': next_page})
        if previous_page is not None:
            links.update({'rel': 'previous', 'href': previous_page})

        if 'links' not in data and not links:
            data.update({'links': []})
        elif 'links' not in data and links:
            data.update({'links': [links]})
        elif links:
            data['links'].append(links)
        return Response(data)

    def get_page_size(self, request):
        # Overwrite the default implementation about the page size as this one
        # don't validate the query parameter, its simply correct it if it is not valid
        # here we want to return a 400 BAD REQUEST when the provided page size is invalid.

        integer_string = request.query_params.get(self.page_size_query_param, self.page_size)

        try:
            page_size = int(integer_string)
        except ValueError as error:
            logger.error(
                'Invalid query parameter limit=%s: must be an integer',
                integer_string,
                extra={'request': request}
            )
            raise ValidationError(_('invalid limit query parameter: must be an integer'))

        if page_size <= 0:
            raise ValidationError(
                _('limit query parameter to small, must be in range 1..%d') % (self.max_page_size)
            )
        if self.max_page_size and page_size > self.max_page_size:
            raise ValidationError(
                _('limit query parameter to big, must be in range 1..%d') % (self.max_page_size)
            )

        return page_size


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    if isinstance(exc, exceptions.APIException):
        status_code = exc.status_code
        description = exc.detail
        if isinstance(description, (list)):
            # Some APIException, like for instance the ValidationError wrap the detail into a list
            # because the STAC API spec wants a string as description we join the list together here
            description = '\n'.join(description)
    elif settings.DEBUG and not settings.DEBUG_PROPAGATE_API_EXCEPTIONS:
        # Other exceptions are left to Django to handle in DEBUG mode, this allow django
        # to set a nice HTML output with backtrace when DEBUG_PROPAGATE_EXCEPTIONS is false
        # With DEBUG_PROPAGATE_API_EXCEPTIONS with can disable this behavior for testing purpose
        return None
    else:
        # Make sure to use a JSON output for other exceptions in production
        description = str(exc)
        status_code = 500

    data = {"code": status_code, "description": description}

    if response is not None:
        # Overwrite the response data
        response.data = data
    else:
        response = Response(data, status=status_code)

    return response
