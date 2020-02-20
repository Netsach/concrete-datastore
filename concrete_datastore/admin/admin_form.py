# coding: utf-8
from django import forms as django_forms
from django.contrib.auth import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django_otp.forms import OTPAuthenticationFormMixin
from django.contrib.auth import get_user_model


class MyAuthForm(forms.AuthenticationForm):
    username = django_forms.EmailField(
        label=_("Email Address"), max_length=254
    )


class OTPAuthenticationForm(MyAuthForm, OTPAuthenticationFormMixin):

    otp_error_messages = {
        'token_required': _('Please enter your OTP token.'),
        'challenge_exception': _('Error generating challenge: {0}'),
        'challenge_message': _(
            'Enter the two authentication code you received by email'
        ),
        'invalid_token': _(
            'Invalid token. Please make sure you have entered it correctly.'
        ),
        'n_failed_attempts': _(
            "Verification temporarily disabled because of %(failure_count)d failed attempt, please try again soon.",
            "Verification temporarily disabled because of %(failure_count)d failed attempts, please try again soon.",
            "failure_count",
        ),
        'verification_not_allowed': _(
            "Verification of the token is currently disabled"
        ),
    }

    otp_token = django_forms.CharField(
        required=False,
        widget=django_forms.TextInput(attrs={'autocomplete': 'off'}),
    )

    # This is a placeholder field that allows us to detect when the user clicks
    # the otp_challenge submit button.
    otp_challenge = django_forms.CharField(required=False)

    def clean(self):
        self.cleaned_data = super().clean()
        self.clean_otp(self.get_user())

        return self.cleaned_data

    def _handle_challenge(self, device):
        try:
            device.generate_challenge()
        except Exception as e:
            # pylint: disable=no-member
            raise django_forms.ValidationError(
                self.otp_error_messages['challenge_exception'].format(e),
                code='challenge_exception',
            )

        #:  If the challenge is successfully generated and in order to show
        #:  the appropriate message, a `ValidationError` must be raised.
        #:  *NB* This validation error does not mean that an error occured
        raise django_forms.ValidationError(
            self.otp_error_messages['challenge_message'],
            code='challenge_message',
        )

    def clean_otp(self, user):
        if user is None:
            return

        device = self._chosen_device(user)
        token = self.cleaned_data.get('otp_token')
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        user.otp_device = None
        try:
            if token:
                user.otp_device = self._verify_token(user, token, device)
                user._is_verified = True
                user.save()
            elif username and password:
                self._handle_challenge(device)
            else:
                raise django_forms.ValidationError(
                    self.otp_error_messages['token_required'],
                    code='token_required',
                )
        finally:
            if user.otp_device is None:
                self._update_form(user)

    def _chosen_device(self, user):
        device = user.emaildevice_set.filter(confirmed=True).last()
        if not device:
            device = user.emaildevice_set.create(
                email=user.email, name='User default email', confirmed=True
            )

        return device

    @staticmethod
    def device_choices(user):
        user_divices = user.emaildevice_set.filter(confirmed=True)
        if not user_divices:
            user_divices = [
                user.emaildevice_set.create(
                    email=user.email, name='User default email', confirmed=True
                )
            ]
        return list((d.persistent_id, d.name) for d in user_divices)


class MyCreationUserForm(forms.UserCreationForm):
    email = django_forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email").lower()
        Concreteuser = get_user_model()
        if Concreteuser.objects.filter(email=email).count() > 0:
            raise django_forms.ValidationError(
                _("A user with this email already exists.")
            )
        return email

    def save(self, commit=True):
        user = super(MyCreationUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        if commit:
            user.save()
        return user


class MyChangeUserForm(forms.UserChangeForm):
    MY_CHOICES = (
        ('SuperUser', 'Super User'),
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('SimpleUser', 'Simple User'),
        ('Blocked', 'Blocked'),
    )

    user_level = django_forms.ChoiceField(choices=MY_CHOICES)

    def __init__(self, *args, **kwargs):
        obj = kwargs.get('instance')
        if obj is not None:
            user_level = ""
            if obj.is_superuser:
                user_level = 'SuperUser'
            elif obj.admin:
                user_level = 'Admin'
            elif obj.is_staff:
                user_level = 'Manager'
            elif obj.is_active:
                user_level = 'SimpleUser'
            else:
                user_level = 'Blocked'
            kwargs['initial'] = {'user_level': user_level}

        super(MyChangeUserForm, self).__init__(*args, **kwargs)
