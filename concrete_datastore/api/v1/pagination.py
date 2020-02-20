# coding: utf-8
from django.conf import settings

from rest_framework import pagination, response


class ExtendedPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return response.Response(
            {
                'objects_count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data,
                'objects_count_per_page': self.page.paginator.per_page,
                'num_total_pages': self.page.paginator.num_pages,
                'num_current_page': self.page.number,
                'max_allowed_objects_per_page': settings.API_MAX_PAGINATION_SIZE,
            }
        )

    def get_page_size(self, request):
        default_page_size = settings.REST_FRAMEWORK.get(
            'PAGE_SIZE', settings.API_MAX_PAGINATION_SIZE
        )
        try:
            page_size = int(
                request.GET.get('c_resp_page_size', default_page_size)
            )
        except ValueError:
            page_size = default_page_size

        if request.GET.get('c_resp_nested', 'true') == 'true':
            page_size = min(settings.API_MAX_PAGINATION_SIZE_NESTED, page_size)
        else:
            page_size = min(settings.API_MAX_PAGINATION_SIZE, page_size)
        return max(1, page_size)
