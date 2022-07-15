# coding: utf-8
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST


class ConcreteBadResponse(Response):
    def __init__(self, message):
        super().__init__(
            data={"message": message, "_errors": ["INVALID_DATA"]},
            status=HTTP_400_BAD_REQUEST,
        )
