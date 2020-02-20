# coding: utf-8
from django.core.exceptions import ValidationError


def validate_file(fieldfile_obj):
    if fieldfile_obj.file is None:  # skip-test-coverage
        raise ValidationError("Erreur : fichier absent.")
