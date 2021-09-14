# coding: utf-8
import json
import logging
import sys
import os
from io import StringIO
from tempfile import NamedTemporaryFile
from django.utils import timezone
from django.core.management import call_command
from django.conf import settings
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseForbidden,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import get_user_model
from concrete_datastore.concrete.models import UserConfirmation, DIVIDER_MODEL

logger = logging.getLogger(__name__)


def email_confirmation_view(request, token):
    confirmation = get_object_or_404(UserConfirmation, pk=token)
    confirmation.confirmed = True
    confirmation.save()
    if confirmation.redirect_to:
        return redirect(confirmation.redirect_to)
    return HttpResponse('Compte confirmé, Account confirmed')


def filter_scopes_for_unsubscribe(queryset, lookup_as_dict):
    return queryset.filter(**lookup_as_dict)


def parse_lookup_for_unsubscribe(model, lookup_as_json, fields):
    try:
        lookup_as_dict = json.loads(lookup_as_json)
        if not isinstance(lookup_as_dict, dict):
            raise json.decoder.JSONDecodeError(
                msg="JSON main object should be a dict",
                doc=lookup_as_dict,
                pos=0,
            )

        for k in lookup_as_dict.keys():
            if k not in fields:
                raise AttributeError(f'{k} not in {model.__name__} fields')

        return lookup_as_dict
    except json.decoder.JSONDecodeError:
        raise AttributeError(
            'Concrete settings '
            'CONCRETE_SCOPES_FILTER_LOOKUP_FOR_UNSUBSCRIBE_JSON '
            'should be a valid json'
        )


def unsubscribe_notifications_view(request, token):
    """
    token is the uid of UserNotificationChoice instance.
    """
    user = get_object_or_404(
        get_user_model(), subscription_notification_token=token
    )
    lookup_as_json = (
        settings.CONCRETE_SCOPES_FILTER_LOOKUP_FOR_UNSUBSCRIBE_JSON
    )

    queryset = getattr(user, '{}s'.format(DIVIDER_MODEL.lower())).all()
    scopes = filter_scopes_for_unsubscribe(
        queryset=queryset,
        lookup_as_dict=parse_lookup_for_unsubscribe(
            model=queryset.model,
            lookup_as_json=lookup_as_json,
            fields=[f.name for f in queryset.model._meta.fields],
        ),
    )
    return render(
        request,
        'mainApp/unsubscribe.html',
        {
            "token": token,
            "user_email": user.email,
            "scopes": scopes,
            'error_message': '',
            'platform_name': settings.PLATFORM_NAME,
        },
    )


def unsubscribe_notifications_result_view(request, token):
    error_message = ''
    try:
        user = get_object_or_404(
            get_user_model(), subscription_notification_token=token
        )
        results = request.POST.dict()
        # Accept integers (0/1)or boolean (False/True) in answer
        unsub_all = bool(results.get('all', 0))
        list_unsub_to_uid = request.POST.getlist('scope', [])

        user.unsubscribe_all = unsub_all
        user.unsubscribe_to.set(list_unsub_to_uid)
        user.save()
    except Exception:
        error_message = "Something went wrong when validating your choice"
        logger.exception(f'Unsubscription failed for user {user}')
    return render(
        request,
        'mainApp/unsubscribe_result.html',
        {
            'error_message': error_message,
            'platform_name': settings.PLATFORM_NAME,
        },
    )


class RedirectStdStreams:
    def __init__(self, stdout=sys.stdout, stderr=sys.stderr):
        self._stdout = stdout
        self._stderr = stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush()
        self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr


def dump_data(request):
    if request.user.is_anonymous is True or request.user.is_superuser is False:
        return HttpResponseForbidden()
    resp = StringIO()
    errors = StringIO()
    try:
        with RedirectStdStreams(stdout=resp, stderr=errors):
            call_command('dumpdata', 'concrete')
        resp_value = resp.getvalue()
        errors_value = errors.getvalue()
        if errors.getvalue():
            return JsonResponse(data={'error': errors_value}, status=400)
        if request.GET.get('download', '').lower() == 'true':
            #: Download the json file
            now = timezone.now()
            filename = 'dump_{}.json'.format(now.strftime("%Y-%m-%d_%H-%M"))
            response = StreamingHttpResponse(resp_value, content_type="json")
            response[
                'Content-Disposition'
            ] = 'attachment; filename="{}"'.format(filename)
            return response

        json_resp = json.loads(resp_value)
        return JsonResponse(
            data={'result': json_resp, 'objects_count': len(json_resp)},
            status=200,
        )
    except Exception as e:
        return JsonResponse(data={'error': str(e)}, status=400)


def load_data(request):
    if request.user.is_anonymous is True or request.user.is_superuser is False:
        return HttpResponseForbidden()

    file = request.FILES.get('json_dump_file')
    if file is None:
        return JsonResponse(data={'error': 'No file was given'}, status=400)
    full_path = ""
    try:
        with NamedTemporaryFile(suffix='.json', mode='w', delete=False) as fd:
            full_path = os.path.join(os.getcwd(), fd.name)
            json.dump(json.loads(file.read().decode('utf-8')), fd)
        resp = StringIO()
        errors = StringIO()
        with RedirectStdStreams(stdout=resp, stderr=errors):
            call_command('loaddata', full_path)
        resp_value = resp.getvalue()
        errors_value = errors.getvalue()
        if errors.getvalue():
            response = JsonResponse(data={'error': errors_value}, status=400)
        else:
            response = JsonResponse(data={'message': resp_value}, status=200)
    except Exception as e:
        response = JsonResponse(
            data={'error': f'An error has occured: {e}'}, status=400
        )
    finally:
        if os.path.exists(full_path):
            os.remove(full_path)
        return response
