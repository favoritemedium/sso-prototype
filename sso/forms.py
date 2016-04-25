from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
import re

from django.db import IntegrityError


# Check only the very basic email format. The real validation happens when
# we actually send to the email address. This will allow  unconventional
# email addresses to still be used.
email_format = re.compile(r'^[^@]+@[^@]+$')

# In addition to checking the email format, also normalie the domain to lower
# case so that yahoo.com and Yahoo.com are recognized as the same.
def emailcleaner(email):
    if not email_format.match(email):
        raise forms.ValidationError(_('Enter a valid email address.'), code='invalid')
    # Note that our regex guarantees the existance of exactly one '@'.
    pre, post = email.split('@')
    return pre + '@' + post.lower()


class SigninForm(forms.Form):
    email = forms.CharField(label="Email", max_length=254)
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    def clean_email(self):
        return emailcleaner(self.cleaned_data['email'])


class SignupForm(forms.Form):
    email = forms.CharField(label="Email", max_length=254)

    def clean_email(self):
        return emailcleaner(self.cleaned_data['email'])


class VerifyForm(forms.Form):
    email = forms.CharField(label="Email", max_length=254, disabled=True)
    password = forms.CharField(label="Password", widget=forms.PasswordInput())
    full_name = forms.CharField(label="Full name", max_length=50, required=False)
    short_name = forms.CharField(label="Short name", max_length=30)
    token = forms.CharField(widget=forms.HiddenInput())
