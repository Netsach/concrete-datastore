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
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
    )

    # This is a placeholder field that allows us to detect when the user clicks
    # the otp_challenge submit button.
    otp_challenge = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
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
            raise ValidationError('OTP authentication already configured')

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
                #: If no username or no password are given, the user
                #: would be None, so this case should never occur,
                #: but we keep it in case it happens
                raise forms.ValidationError(  # pragma: no cover
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

    def get_user(self):
        return self.user_cache
