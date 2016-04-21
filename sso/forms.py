from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
import re

from .models import Member
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

    def clean(self):
        super(SigninForm, self).clean()

        # If either email or password has failed validatation (e.g. is missing),
        # then we quit here.
        # em, pw = self.cleaned_data.get('email'), self.cleaned_data.get('password')
        #if not (em and pw):
        if self.errors:
            return

        # We have both email and password; attempt to authenticate.
        member = authenticate(email=em, password=pw)
        if member is None:
            raise forms.ValidationError(_("Email and password don't match."), code='auth_failure')
        elif not member.is_active:
            raise forms.ValidationError(_("That account is inactive."), code='inactive_account')

        # Authentication is successful, so store the member object along with
        # the cleaned data.  The view will then use this to call auth.login.
        self.cleaned_data['member'] = member


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

    def clean(self):
        super(VerifyForm, self).clean()

        if self.errors:
            return

        member = Member(
            email=self.cleaned_data['email'],
            full_name=self.cleaned_data['full_name'],
            short_name=self.cleaned_data['short_name'],
        )
        member.set_password(self.cleaned_data['password'])
        try:
            member.save()
        except IntegrityError:
            raise forms.ValidationError(_("That email is already registered."), code='duplicate')

        self.cleaned_data['member'] = authenticate(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'])
