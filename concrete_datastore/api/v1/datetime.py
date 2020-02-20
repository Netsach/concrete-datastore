# coding: utf-8
import pendulum

api_format = '%Y-%m-%dT%H:%M:%SZ'


def format_datetime(dt):
    return ensure_pendulum(dt).format(api_format, formatter='classic')


def ensure_pendulum(value):
    d = value
    if isinstance(d, str):
        d = pendulum.parse(d)
    if not isinstance(d, pendulum.pendulum.Pendulum):
        d = pendulum.instance(d)
    return d
