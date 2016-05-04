import json
import os.path
from django.apps import AppConfig
from fmproject import settings


class SsoConfig(AppConfig):
    base_config = json.load(
        open(os.path.join(settings.BASE_DIR, 'fmproject', 'config.json'))
    )
    name = 'sso'

    github_client_id = base_config['github']['client_id']
    github_client_secret = base_config['github']['client_secret']

    google_client_id = base_config['google']['client_id']
    google_client_secret = base_config['google']['client_secret']

    facebook_client_id = base_config['facebook']['client_id']
    facebook_client_secret = base_config['facebook']['client_secret']

