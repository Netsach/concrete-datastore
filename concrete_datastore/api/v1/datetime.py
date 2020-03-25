# coding: utf-8
import pendulum

api_format = 'YYYY-MM-DDTHH:mm:ss\Z'


def format_datetime(dt):
    return ensure_pendulum(dt).format(api_format)


def ensure_pendulum(value):
    d = value
    if isinstance(d, str):
        d = pendulum.parse(d)
    if not isinstance(d, pendulum.Date):
        d = pendulum.instance(d)
    return d
