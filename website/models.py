
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from django_extensions.db.models import TimeStampedModel


class CustomUser(AbstractUser, TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
