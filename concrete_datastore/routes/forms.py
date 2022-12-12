# conding: utf-8
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import ngettext_lazy, gettext_lazy as _
from concrete_datastore.concrete.constants import MFA_OTP, MFA_EMAIL


class ConfigureOTPLoginForm(forms.Form):

    otp_error_messages = {
        'token_required': _('Please enter your OTP token.'),
        'challenge_exception': _('Error generating challenge: {0}'),
        'challenge_message_email': _(
            'Enter the two authentication code you received by email'
        ),
        'invalid_token': _(
            'Invalid token. Please make sure you have entered it correctly.'
        ),
        'n_failed_attempts': ngettext_lazy(
            "Verification temporarily disabled because of %(failure_count)d failed attempt, please try again soon.",
            "Verification temporarily disabled because of %(failure_count)d failed attempts, please try again soon.",
            "failure_count",
        ),
        'verification_not_allowed': _(
            "Verification of the token is currently disabled"
        ),
        'otp_already_configured': _('OTP authentication already configured'),
        'wrong_auth_credentials': _('Wrong auth credentials'),
    }
    email = forms.EmailField(label="Email", max_length=254)
    password = forms.CharField(label="Password", max_length=254)

    otp_token = forms.CharField(
        required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )

    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        otp_token = cleaned_data.get("otp_token")
        User = get_user_model()
        self.user_cache = User.objects.filter(email=email).first()
        if self.user_cache is None:
            raise ValidationError(
                self.otp_error_messages['wrong_auth_credentials'],
                code='wrong_auth_credentials',
            )
        if self.user_cache.check_password(password) is False:
            #: Clear user cache to reset the form
            self.user_cache = None
            raise ValidationError(
                self.otp_error_messages['wrong_auth_credentials'],
                code='wrong_auth_credentials',
            )
        otp_device = self.user_cache.emaildevice_set.filter(
            mfa_mode=MFA_OTP, confirmed=True
        ).first()
        if otp_device:
            #: Clear user cache to reset the form
            self.user_cache = None
            raise ValidationError(
                self.otp_error_messages['otp_already_configured'],
                code='otp_already_configured',
            )
        device = self._chosen_device(self.user_cache)
        if not otp_token:
            self._handle_challenge(device)
        else:
            verified = device._verify_email_token(otp_token)
            if verified is False:
                #: Keep user cache to avoid selecting an email and password
                raise ValidationError(
                    self.otp_error_messages['invalid_token'],
                    code='invalid_token',
                )
        return cleaned_data

    def _handle_challenge(self, device):
        try:
            device.generate_challenge()
        except Exception as e:
            raise forms.ValidationError(
                self.otp_error_messages['challenge_exception'].format(e),
                code='challenge_exception',
            )

        #:  If the challenge is successfully generated and in order to show
        #:  the appropriate message, a `ValidationError` must be raised.
        #:  *NB* This validation error does not mean that an error occured
        raise forms.ValidationError(
            self.otp_error_messages['challenge_message_email'],
            code='challenge_message_email',
        )

    def _chosen_device(self, user):
        device = user.emaildevice_set.filter(
            confirmed=True, mfa_mode=MFA_EMAIL
        ).first()
        if not device:
            device = user.emaildevice_set.create(
                email=user.email, name='User default email', confirmed=True
            )

        return device

    def get_user(self):
        return self.user_cache
