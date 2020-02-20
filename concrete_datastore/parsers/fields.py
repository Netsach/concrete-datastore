# coding: utf-8
from __future__ import unicode_literals, absolute_import, print_function


class FieldDescriptor:
    """
    Field descriptor base class
    """

    def __init__(self, name, *args, **kwargs):
        self.name = name

    def __get__(self, instance, cls=None):
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value


class RelFieldDescriptor(FieldDescriptor):
    """
    Field descriptor for related data (rel_single)
    """

    pass


class RelIterableFieldDescriptor(FieldDescriptor):
    """
    Field descriptor for related data (rel_single)
    """

    def __get__(self, instance, cls=None):
        if instance.__dict__.get(self.name) is None:
            instance.__dict__[self.name] = set([])

        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        raise AttributeError(
            'Cannot use set method. Use .add(*objects) and .remove(*objects)'
        )


field_descriptors = {
    'data': FieldDescriptor,
    'rel_single': RelFieldDescriptor,
    'rel_iterable': RelIterableFieldDescriptor,
}


def get_field_descriptor(f_type):
    if f_type == 'fk':
        return RelFieldDescriptor
    if f_type == 'm2m':
        return RelIterableFieldDescriptor
    return FieldDescriptor
