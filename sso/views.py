import os
import hashlib
import requests
import facebook
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .forms import SigninForm, SignupForm, VerifyForm
from .models import Member, VerifyEmail
from .mail import send_verify_link, send_reset_password_link
from sso.apps import SsoConfig



def main(request):
    # The authentication middleware adds the current member to the request
    # object as request.user.  We can check request.user.is_authenticated()
    # to determine if someone is signed in or not.  (This can also be done
    # within the tempate.)

    if request.user.is_authenticated():
        # do something here
        pass

    return render(request, 'sso/main.html')


@csrf_protect
def signin(request):
    """
    This is the basic sign-in view.  When called as a GET, a blank sign-in form
    (and optionally a blank sign-up form) is displayed.  When called as a POST
    with valid credentials, then the user is signed in.  When called as a POST
    with invalid credentials, the form is re-displayed for correction.
    """
    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            member = authenticate(email=form.cleaned_data['email'],
                password=form.cleaned_data['password'])
            if member is None:
                form.add_error("password", "Email and password don't match.")
            elif not member.is_active:
                form.add_error("email", "That account is disabled.")
            else:
                login(request, member)
                return HttpResponseRedirect('/')
    else:
        form = SigninForm()

    # Depending on design requirements, the sign-in page can include either
    # a blank sign-up form or a link to the sign-up page.
    return render(request, 'sso/signin.html',
        {
            'signinform': form,
            'signupform': SignupForm(),
            'github_client_id': SsoConfig.github_client_id,
            'facebook_client_id': SsoConfig.facebook_client_id
        })


def signout(request):
    """
    Signs out the current user and returns to the main page.
    """
    logout(request)
    return HttpResponseRedirect('/')


@csrf_protect
def signup(request):
    """
    This is the basic sign-up view.  When called as a GET, a blank sign-up form
    is displayed.  When called as a POST with a valid email, a confirmation
    token is generated and a confirmation email is sent out.  When called as a
    POST without a valid email, the form is re-displayed for correction.
    An email that is already registered is considered invalid.
    """
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if Member.objects.is_registered(email):
                form.add_error("email", "That email address is already registered.")
            else:
                token = VerifyEmail.generate_token(email)
                send_verify_link(request, email, token)
                return render(request, 'sso/checkyouremail.html', {'email': email})
    else:
        form = SignupForm()

    return render(request, 'sso/signin.html',
        {'signinform': SigninForm(), 'signupform': form})


@csrf_protect
def verify(request):
    """
    This is the entry point for the verify link that's sent by
    send_verify_link() above.

    When the user clicks on the link in the email, we get a GET request
    with the verify token as a URL parameter.  This token is then embedded
    into the form, so we get it again (in the POST data) when the user has
    filled in their name, password, and any other requested info.

    The token is reused this way in order to not rely on the session to
    keep track of what email address has just been verified.
    """
    if request.method == 'POST':
        token = request.POST.get('token','')
    else:
        token = request.GET.get('token','')

    email = VerifyEmail.redeem_token(token)
    if email is None:
        # Sorry, the link is wrong or expired.
        return render(request, 'sso/verifysorry.html',
            {'code': 'invalid_token'})
    if Member.objects.is_registered(email):
        # Edge case: Somehow the email already got registered (e.g. the user
        # had an extra tab open).
        return render(request, 'sso/verifysorry.html',
            {'email': email, 'code': 'duplicate'})

    if request.method == 'POST':
        form = VerifyForm(request.POST, initial={'email': email})
        if form.is_valid():
            # Now we have the rest of the required info for sign-up, so
            # create the member.
            args = form.cleaned_data.copy()
            args.pop('token')
            Member.objects.create_user(**args)
            member = authenticate(email=args['email'], password=args['password'])
            # TODO: what if authenticate fails?
            login(request, member)
            return HttpResponseRedirect('/welcome')
    else:
        form = VerifyForm(initial={'email': email, 'token': token})

    return render(request, 'sso/signup-step2.html', {'form': form})


@login_required
def welcome(request):
    return render(request, 'sso/welcome.html')


def request_access_token(url, payload):
    headers = {
        'Accept': 'application/json'
    }
    r = requests.post(url, data=payload, headers=headers)
    return r.json()


def auth_with_github(request):
    code = request.GET.get('code', '')
    if code is not '':
        payload = {
            'client_id': SsoConfig.github_client_id,
            'client_secret': SsoConfig.github_client_secret,
            'code': code,
        }
        json_resp = request_access_token('https://github.com/login/oauth/access_token', payload)
        token = json_resp['access_token']
        scopes = json_resp['scope'].split(',')

        primary_email = get_github_primary_user_email(token)
        return JsonResponse({'result': primary_email})
    else:
        return JsonResponse({'error': 'Error'})


def get_github_primary_user_email(token):
    r = requests.get('https://api.github.com/user/emails',
                     params={
                         'access_token': token
                     })
    user_email_list = r.json()
    primary_email = ''
    for email_info in user_email_list:
        if email_info.get('primary', ''):
            return email_info['email']

    return primary_email
######################################
# Facebook related code
######################################
def auth_with_facebook(request):
    code = request.GET.get('code', '')
    if code is not '':
        payload = {
            'client_id': SsoConfig.facebook_client_id,
            'client_secret': SsoConfig.facebook_client_secret,
            'code': code,
            'redirect_uri': 'http://localhost:8000/callback/facebook',
        }
        json_resp = request_access_token(
            'https://graph.facebook.com/v2.6/oauth/access_token',
            payload
        )

        token = json_resp['access_token']
        graph = facebook.GraphAPI(access_token=token)
        args = {'fields' : 'id,name,email', }
        profile = graph.get_object(id='me', **args)

        return JsonResponse(profile)
        #scopes = json_resp['scope'].split(',')

        #primary_email = get_github_primary_user_email(token)
        #return JsonResponse({'result': primary_email})
    else:
        return JsonResponse({'error': 'Error'})


