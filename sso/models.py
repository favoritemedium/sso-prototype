from django.db import models, IntegrityError
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import string
import random
import time
import re

class MemberManager(BaseUserManager):

    def create_user(self, email, short_name, password=None):
        """
        Creates and saves a user with the given email and short name.
        """
        if not email:
            raise ValueError('Members must have an email address')

        member = self.model(
            email=self.normalize_email(email),
            short_name=short_name,
        )

        member.set_password(password)
        member.save(using=self._db)
        return member

    def create_superuser(self, email, short_name, password):
        """
        Creates and saves a superuser with the given email, short name
        and password.
        """
        member = self.create_user(
            email=self.normalize_email(email),
            password=password,
            short_name=short_name,
        )
        member.is_admin = True
        member.save(using=self._db)
        return member


class Member(AbstractBaseUser):
    # members are identified by email address
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("That email is already registered."),
        },
    )
    full_name = models.CharField(_('full name'), max_length=50, blank=True)
    short_name = models.CharField(_('short name'), max_length=30)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['short_name']

    objects = MemberManager()

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.short_name or self.full_name

    @property
    def is_staff(self):
        "Is the member staff?"
        return self.is_admin

    def has_perm(self, perm, obj=None):
        "Does the member have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the member have permissions to view the app `app_label`?"
        return True

    def __str__(self):
        return self.email



# The default is for tokens to be valid up to 24 hours after issue.
EMAIL_TOKEN_VALIDITY = 24 * 3600   # Tokens are valid for 24 hours

# Tokens are a random string of 64 letter/numbers.  This is overkill.
EMAIL_TOKEN_LENGTH = 64

# Don't expire a token immediately after its checked.  Give the user
# up to ten extra minutes to complete the signup process.
SIGNUP_GRACE_TIME = 10 * 60

# Generates a random token.
def create_token():
    return ''.join(random.choice(string.ascii_letters + string.digits) \
        for _ in range(EMAIL_TOKEN_LENGTH))

# Check only the very basic email format. The real validation happens when
# we actually send to the email address. This will allow  unconventional
# email addresses to still be used.
email_format = re.compile(r'^[^@]+@[^@]+$')

class VerifyEmail(models.Model):
    """
    Class VerifyEmail generates random tokens that are associated with email
    addresses.  The tokens may then be mailed to the email address to verify
    that the user owns the address.
    """
    email = models.EmailField()
    token = models.CharField(max_length=EMAIL_TOKEN_LENGTH, unique=True)

    def expires_default():
        return int(time.time()) + EMAIL_TOKEN_VALIDITY
    expires = models.BigIntegerField(default=expires_default)

    @classmethod
    def get_token(cls, email):
        """
        Generate an email verify token.  This token should then be emailed to
        the user as part of a verify link.
        """
        if not email_format.match(email):
            raise ValidationError(_('Enter a valid email address.'), code='invalid')

        # Normalize the domain part of the email so that we recognize
        # yahoo.com and Yahoo.com as the same.
        # Our email_format regex check has ensured that the email string
        # exactly one '@'
        pre, post = email.split('@')
        email = pre + '@' + post.lower()

        done = False
        while not done:
            token = create_token()
            try:
                cls(email=email, token=token).save()
                done = True
            except IntegrityError:
                # catch a duplicate token
                pass

        return token

    @classmethod
    def verify_token(cls, token):
        """
        Finds an email address associated with a verify token.  This should be
        called when a user clicks on a link in their email.
        Returns None if the token is not valid.
        """
        now = int(time.time())
        ve = cls.objects.filter(token=token, expires__gte=now).first()
        if ve is None:
            return None

        # Since we've just now fetched it, make sure it's not about to expire.
        # Give the user at least ten minutes to finish sign-up.
        if ve.expires < now + SIGNUP_GRACE_TIME:
            ve.expires = now + SIGNUP_GRACE_TIME
            ve.save()

        return ve.email

    @classmethod
    def remove(cls, email):
        """
        Removes an email from the to-verify list.
        This should be called when a user finishes registration and signs in,
        as it's no longer necessary to verify their email.
        """
        cls.objects.filter(email=email).delete()

    @classmethod
    def cron(cls):
        """
        Call this regularly to clean out unused tokens.
        """
        cls.objects.filter(expires__lt=int(time.time())).delete()

    def __str__(self):
        return self.email + ' expires ' + \
            time.strftime('%H:%M', time.gmtime(self.expires))


