# coding: utf-8
import json
import logging

from django.conf import settings
from django.http import HttpResponse
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
