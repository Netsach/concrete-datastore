# coding: utf-8
import pendulum
import datetime
from typing import Iterable, Dict
from django.utils import timezone
from django.http import StreamingHttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import translation


def translate_if_date(language, field):
    if language and isinstance(field, datetime.datetime):
        try:
            field = pendulum.parse(str(field)).format(
                "DD/MM/YYYY HH:mm:ss", locale=language
            )
        except Exception:
            pass
    return str(field)  # i18n translation only works if the value is a string


def csv_data_generator(
    queryset: Iterable[Dict], fields: Iterable[str], language=None
):
    """
    Generator producing UTF-8 - quoted and semicolon separated CSV
    """
    if language:
        translation.activate(language)

    # Yields headers
    yield '{}\n'.format(';'.join('"{}"'.format(_(field)) for field in fields))

    # Yields rows
    for item in queryset:
        value = '{}\n'.format(
            ';'.join(
                [
                    '"{}"'.format(
                        _(translate_if_date(language, item.get(field, '')))
                    )
                    for field in fields
                ]
            )
        ).encode('utf-8')
        yield value


def csv_streaming_response(
    queryset, fields: Iterable[str], filename: str = None, language=None,
):
    if filename is None:
        now = timezone.now()
        filename = f'export_{queryset.model.__name__}_{now.strftime("%Y-%m-%d_%H-%M")}.csv'
        if language:
            filename = f'export_{language}_{queryset.model.__name__}_{now.strftime("%Y-%m-%d_%H-%M")}.csv'

    response = StreamingHttpResponse(
        csv_data_generator(queryset, fields, language),
        content_type="text/csv",
    )

    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        filename
    )

    return response
