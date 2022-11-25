# conding: utf-8
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django import forms


class ConfigureOTPLoginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)
    password = forms.CharField(label="Password", max_length=254)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user is None:
            raise ValidationError('Wrong auth credentials')
        if user.check_password(password) is False:
            raise ValidationError('Wrong auth credentials')
