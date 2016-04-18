# SSO Prototype

This is a simple single-sign-on prototype
that can be used as base user authentication system for just about anything.

## Recommended local setup

    $ virtualenv -p python3 sso
    $ source sso/bin/activate
    $ pip install -r requirements.txt
    $ ./manage.py migrate

I like to use [autoenv](https://github.com/kennethreitz/autoenv)
with an `.env` file that looks like this:

    source `dirname -- "$0"`/sso/bin/activate
    alias pm="./manage.py"
    export DEBUG=on

Then I can cd into project root and run the site in debug mode with:

    $ pm runserver
