# conding: utf-8
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django import forms
from concrete_datastore.concrete.constants import MFA_OTP
from django.utils.translation import ngettext_lazy, gettext_lazy as _
from concrete_datastore.concrete.constants import MFA_EMAIL


class ConfigureOTPLoginForm(forms.Form):
    """
    TODO:
    Create a code with an emaildevice with MFA_EMAIL.
    Retrieve the last emaildevice with MFA_EMAIL (do not check the field `confirmed`)
    or create it if it does not exist and generate a challenge.
    Then verify the code with the same device when the user is authenticated
    """

    otp_error_messages = {
        'token_required': _('Please enter your OTP token.'),
        'challenge_exception': _('Error generating challenge: {0}'),
        'challenge_message_email': _(
            'Enter the two authentication code you received by email'
        ),
        'challenge_message_otp': _(
            'Enter the two-factor authentication code from a configured OTP application'
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
            raise ValidationError('Wrong auth credentials')
        if self.user_cache.check_password(password) is False:
            raise ValidationError('Wrong auth credentials')
        otp_device = self.user_cache.emaildevice_set.filter(
            mfa_mode=MFA_OTP, confirmed=True
        ).first()
        if otp_device:
            #: Clear user cache to reset the form
            self.user_cache = None
            raise ValidationError('OTP authentication already configured')
        if not otp_token:
            device = self._chosen_device(self.user_cache)
            self._handle_challenge(device)
        return cleaned_data

    def _handle_challenge(self, device):
        challenge_message_name = 'challenge_message_otp'
        if device.mfa_mode == MFA_EMAIL:
            challenge_message_name = 'challenge_message_email'
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
            self.otp_error_messages[challenge_message_name],
            code=challenge_message_name,
        )

    def _chosen_device(self, user):
        device = user.emaildevice_set.filter(confirmed=True).last()
        if not device:
            device = user.emaildevice_set.create(
                email=user.email, name='User default email', confirmed=True
            )

        return device

    def get_user(self):
        return self.user_cache
