from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .forms import SigninForm, SignupForm, VerifyForm
from .models import VerifyEmail
from .mail import send_verify_link, send_reset_password_link



def main(request):
    # The authentication middleware adds the current member to the request
    # object as request.user.  We can check request.user.is_authenticated()
    # to determine if someone is signed in or not.  (This can also be done
    # within the template.)

    if request.user.is_authenticated():
        # do something here
        pass

    return render(request, 'sso/main.html')


@csrf_protect
def signin(request):
    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            # The signin form validation includes checking the credentials
            # against the member database.  It it succeeds, then we know we
            # have a valid member.
            login(request, form.cleaned_data['member'])
            return HttpResponseRedirect('/')
    else:
        form = SigninForm()

    return render(request, 'sso/signin.html',
        {'signinform': form, 'signupform': SignupForm()})


def signout(request):
    logout(request)
    return HttpResponseRedirect('/')


@csrf_protect
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():

            # TODO check for duplicate email here (or there)

            email = form.cleaned_data['email']
            send_verify_link(request, email)
            return render(request, 'sso/checkyouremail.html', {'email': email})
    else:
        form = SignupForm()

    return render(request, 'sso/signin.html',
        {'signinform': SigninForm(), 'signupform': form})


@csrf_protect
def verify(request):
    # When the user clicks on the link in the email, we get a GET request
    # with the verify token as a URL parameter.  This token is then embedded
    # into the form, so we get it again (in the POST data) when the user has
    # filled in their name and other info.
    #
    # The token is reused this way in order to not rely on the session to
    # keep track of what email address has just been verified.
    if request.method == 'POST':
        token = request.POST.get('token','')
    else:
        token = request.GET.get('token','')

    email = VerifyEmail.redeem_token(token)
    if email is None:
        # Sorry, the link is wrong or expired.
        return render(request, 'sso/verifysorry.html')

    # TODO check if the email has been registered and make another sorry page.

    if request.method == 'POST':
        form = VerifyForm(request.POST, initial={'email': email})
        if form.is_valid():
            # The form validation creates the new member if all the fields
            # check out, so let's sign the member in an go to the welcome page.
            login(request, form.cleaned_data['member'])
            return HttpResponseRedirect('/welcome')
    else:
        form = VerifyForm(initial={'email': email, 'token': token})

    return render(request, 'sso/signup-step2.html', {'form': form})


@login_required
def welcome(request):
    return render(request, 'sso/welcome.html')
