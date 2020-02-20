# coding: utf-8
import django.dispatch

user_logged_in = django.dispatch.Signal(providing_args=["user"])
