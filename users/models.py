from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid


class UserManager(BaseUserManager):

    use_in_migrations = True

    def create_user(self, email, username, user_profile_image, password=None):

        if not email:
            raise ValueError("must have user email")
        user = self.model(email=self.normalize_email(email), username=username)
        user.uuid = str(uuid.uuid4())
        user.user_profile_image = user_profile_image
        user.login_route = "GOOGLE"
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):

        user = self.create_user(
            email=self.normalize_email(email), username=username, password=password
        )
        user.uuid = str(uuid.uuid4())
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    id = models.AutoField(primary_key=True)
    email = models.EmailField(
        max_length=255,
        unique=True,
    )
    username = models.CharField(
        max_length=20,
        null=False,
    )
    uuid = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    login_route = models.CharField(max_length=10)
    user_profile_image = models.CharField(max_length=300, null=True)
    description = models.TextField(null=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class EmailCode(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=30)
    code = models.CharField(max_length=6)
    timestamp = models.DateTimeField(auto_now_add=True)
