# coding: utf-8
from django.shortcuts import HttpResponse

from social_core.exceptions import SocialAuthBaseException
from social_django.middleware import SocialAuthExceptionMiddleware
from social_core.backends.gitlab import GitLabOAuth2


class SocialCustomAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        if isinstance(exception, SocialAuthBaseException):
            return HttpResponse('Denied ({})'.format(exception))
        return super().process_exception(request, exception)


class NetsachGitLabOAuth2(GitLabOAuth2):
    name = 'gitlab'
    API_URL = 'https://git.netsach.info'
    AUTHORIZATION_URL = 'https://git.netsach.info/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://git.netsach.info/oauth/token'  # nosec
