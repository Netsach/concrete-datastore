# coding: utf-8
from typing import Iterable, Dict
from django.utils import timezone
from django.http import StreamingHttpResponse


def csv_data_generator(iterable: Iterable[Dict], fields: Iterable[str]):
    """
    Generator producing UTF-8 - quoted and semicolon separated CSV
    """

    # Yields headers
    yield '{}\n'.format(
        ';'.join('"{}"'.format(field) for field in fields)
    ).encode('utf-8')

    # Yields rows
    for item in iterable:
        value = '{}\n'.format(
            ';'.join(['"{}"'.format(item.get(field, '')) for field in fields])
        ).encode('utf-8')
        yield value


def csv_streaming_response(
    request, queryset, fields: Iterable[str], filename: str = None
):
    if filename is None:
        now = timezone.now()
        filename = 'export_{}_{}.csv'.format(
            queryset.model.__name__, now.strftime("%Y-%m-%d_%H-%M")
        )

    response = StreamingHttpResponse(
        csv_data_generator(queryset, fields), content_type="text/csv"
    )
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        filename
    )

    return response
