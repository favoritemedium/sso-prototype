# SSO Prototype

This is a simple single-sign-on prototype
that can be used as base user authentication system for just about anything.

## Recommended local setup

    $ virtualenv -p python3 .venv --prompt="(sso) "
    $ source .venv/bin/activate
    $ pip install -r requirements.txt
    $ ./manage.py migrate

I like to use [autoenv](https://github.com/kennethreitz/autoenv)
with an `.env` file that looks like this:

    source `dirname -- "$0"`/.venv/bin/activate
    alias pm="./manage.py"
    export DEBUG=on

This app needs Github app for 3rd part login, please [register your
app](https://github.com/settings/applications/new), and set `/callback/github`
as callback address. After registration done, copy
`fmproject/config.json.example` to `fmproject/config.json` and fill *client_id*
and *client_secret* from registered app to that file.

Then I can cd into project root and run the site in debug mode with:

    $ pm runserver
