from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy as _

# Create your models here.

class UserManager(BaseUserManager):

    def create_user(self, email, short_name, password=None):
        """
        Creates and saves a user with the given email and short name.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            short_name=short_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, short_name, password):
        """
        Creates and saves a superuser with the given email, short name
        and password.
        """
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            short_name=short_name,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    # users are identified by email address
    email = models.EmailField(
        _('email address'),
        unique=True,
        validators=[validate_email],
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

    objects = UserManager()

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.short_name or self.full_name

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.is_admin

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    def __str__(self):
        return self.email

