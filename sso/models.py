from django.db import models, IntegrityError
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import string
import random
import time
import re


# =========================
# Member management section
# =========================

class MemberManager(BaseUserManager):

    def create_user(self, email, short_name, password=None, full_name=''):
        """
        Creates and saves a user with the given email and short name.
        Optionally includes password and full name.
        """
        if not email:
            raise ValueError('Members must have an email address')

        member = self.model(
            email=self.normalize_email(email),
            short_name=short_name,
            full_name=full_name,
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

    def is_registered(self, email):
        """
        Returns True if the email is registered in the member database.
        """
        return self.filter(email=email).count() > 0


class Member(AbstractBaseUser):

    # Members are identified by email address.
    email = models.EmailField(max_length=254, unique=True)

    # By default, we require only a short_name used for greeting,
    # as in "Hi, <name>."
    full_name = models.CharField(max_length=64, blank=True)
    short_name = models.CharField(max_length=32)

    # Setting is_active to False effectively deletes a member but without
    # losing any of their data.
    is_active = models.BooleanField(default=True)

    # The is_admin flag is to allow access to the django admin panel and
    # is intended only for site admins.
    # For other types of admin functions, use the roles field.
    is_admin = models.BooleanField(default=False)

    # This is a bit field to keep track of other roles that the member has,
    # e.g. staff, teacher, gold member.  (This is in place of using the
    # groups function, which is overkill for most of our projects.)
    roles = models.PositiveSmallIntegerField(default=0)

    def has_role(self, role):
        """
        Returns True if this member has any of the roles requested.
        Parameter role is a bitmask.
        """
        return bool(roles & role)

    def has_roles(self, roles):
        """
        Returns True if the member has all of the roles requested.
        Parameter role is a bitmask.
        """
        return roles & role == roles

    # These are used by django admin.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['short_name']

    objects = MemberManager()

    def get_full_name(self):
        return self.full_name or self.short_name

    def get_short_name(self):
        return self.short_name

    # TODO: do we need these?
    # @property
    # def is_staff(self):
    #     "Is the member staff?"
    #     return self.is_admin

    # def has_perm(self, perm, obj=None):
    #     "Does the member have a specific permission?"
    #     return True

    # def has_module_perms(self, app_label):
    #     "Does the member have permissions to view the app `app_label`?"
    #     return True

    def __str__(self):
        return self.email


# ==========================
# Email verification section
# ==========================

# The default is for tokens to be valid up to 24 hours after issue.
EMAIL_TOKEN_VALIDITY = 24 * 3600   # Tokens are valid for 24 hours

# Tokens are a random string of 64 letter/numbers.  This is overkill.
EMAIL_TOKEN_LENGTH = 64

# Don't expire a token immediately after its checked.  Give the user
# up to ten extra minutes to complete the signup process.
SIGNUP_GRACE_TIME = 10 * 60


# Generate a random toke
def create_token():
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(EMAIL_TOKEN_LENGTH))


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
    def generate_token(cls, email):
        """
        Generate an email verify token.  This token should then be emailed to
        the user as part of a verify link.
        """
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
    def redeem_token(cls, token):
        """
        Finds an email address associated with a verify token.
        This should be called when a user clicks on a link in their email.
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


