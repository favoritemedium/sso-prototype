from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import SigninForm, SignupForm
from .models import VerifyEmail

# Create your views here.

def signin(request):
    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            member = authenticate(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'])
            if member is None:
                form.add_error('email', "Email and password don't match.")
            elif not member.is_active:
                form.add_error('email', "That account is inactive.")
            else:
                login(request, member)
                return HttpResponseRedirect('/welcome')
    else:
        form = SigninForm()

    return render(request, 'sso/signin.html',
        {'signinform': form, 'signupform': SignupForm()})

def signout(request):
    logout(request)
    return HttpResponseRedirect('/')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            token = VerifyEmail.get_token(email)
            send_mail(
                'FMProject Registration',
                render_to_string('sso/emailverify', {'link': request.build_absolute_uri('/verify?token=' + token)}),
                'noreply@example.com',
                (email,),
            )
            return render(request, 'sso/checkyouremail.html', {'email': email})
    else:
        form = SignupForm()

    return render(request, 'sso/signin.html',
        {'signinform': SigninForm(), 'signupform': form})

def verify(request):
    if request.method == 'POST':
        token = request.POST.get('token','')
    else:
        token = request.GET.get('token','')

    email = verify_token(token)
    if email is None:
        return render(request, 'sso/verifysorry.html')

    if request.method == 'POST':
        form = VerifyForm(request.POST)
        if form.is_valid():
            # create the new member
            return HttpResponseRedirect('/welcome')
    else:
        form = VerifyForm(initial={'email': email, 'token': token})

    return render(request, 'sso/signup_step2.html', {form: form})

@login_required
def welcome(request):
    return render(request, 'sso/welcome.html')
