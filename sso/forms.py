from django import forms
from django.core.validators import validate_email

class SigninForm(forms.Form):
    email = forms.CharField(label="email", max_length=254)
    password = forms.CharField(label="password", widget=forms.PasswordInput())

class SignupForm(forms.Form):
    email = forms.CharField(label="email", max_length=254, validators=[validate_email])
