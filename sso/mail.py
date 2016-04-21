from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import VerifyEmail

# TODO: move this into settings
MAIL_FROM = "noreply@example.com"


VERIFY_EMAIL_SUBJECT = "Welcome to FM Proejct!"

# Send a request to verify email.  Used for signing up new members.
def send_verify_link(request, email):
    token = VerifyEmail.generate_token(email)
    send_mail(
        VERIFY_EMAIL_SUBJECT,
        render_to_string('sso/emailverify', {'link': request.build_absolute_uri('/verify?token=' + token)}),
        MAIL_FROM,
        (email,),
    )


RESET_PASSWORD_SUBJECT = "Reset your FM Project password"

# Send an email with a link to reset password
def send_reset_password_link(request, email):
    pass
