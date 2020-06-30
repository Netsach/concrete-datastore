# coding: utf-8
from typing import Iterable, Dict
import pendulum
import datetime
from django.utils import timezone
from django.http import StreamingHttpResponse
from django.conf import settings


def translate(field, language=None, isheader=False):
    if language:
        translations = settings.TRANSLATIONS.get(language)
        if translations:
            if isheader:
                if translations.get(field):
                    return translations.get(field)
            else:
                if isinstance(field, bool) and translations.get(str(field)):
                    return translations.get(str(field))
                if isinstance(field, datetime.datetime):
                    try:
                        dt = pendulum.parse(str(field))
                        return dt.format(
                            "DD/MM/YYYY HH:mm:ss", locale=language
                        )
                    except Exception:
                        pass
    return field


def csv_data_generator(
    queryset: Iterable[Dict], fields: Iterable[str], language=None
):
    print(f'generate csv for language {language}')
    """
    Generator producing UTF-8 - quoted and semicolon separated CSV
    """

    # Yields headers
    yield '{}\n'.format(
        ';'.join(
            '"{}"'.format(translate(field, language, True)) for field in fields
        )
    ).encode('utf-8')

    # Yields rows
    for item in queryset:
        value = '{}\n'.format(
            ';'.join(
                [
                    '"{}"'.format(translate(item.get(field, ''), language))
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
