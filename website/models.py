
import uuid

import pendulum

from django.db import transaction
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator

from django_extensions.db.models import TimeStampedModel


class CustomUser(AbstractUser, TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


def generate_setting_name():
    return "Conf du {:%d/%m/%y}".format(pendulum.utcnow())


class Settings(TimeStampedModel):

    class Meta:
        verbose_name = "Configuration"

    name = models.CharField(
        verbose_name="Nom de cette configuration",
        max_length=128,
        default=generate_setting_name
    )

    active = models.BooleanField(
        default=True,
        verbose_name="Activer cette configuration"
    )

    sirene_ftp_ip_address = models.GenericIPAddressField(
        protocol='IPv4',
        verbose_name="Adresse IP du FTP SIRENE",
        blank=True,
        null=True
    )

    sirene_ftp_port = models.PositiveIntegerField(
        verbose_name="Port du FTP SIRENE",
        default=21,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1)
        ]
    )

    sirene_ftp_username = models.CharField(
        verbose_name="Login du FTP SIRENE",
        max_length=128,
        blank=True,
        null=True
    )

    sirene_ftp_password = models.CharField(
        verbose_name="Mot de passe du FTP SIRENE",
        max_length=128,
        blank=True,
        null=True
    )

    sirene_csv_file_path = models.CharField(
        verbose_name="Chemin du fichier CSV de SIRENE",
        default="VTM_ATTENDUS_PILOTAGE_V2.csv",
        max_length=512,
        blank=True,
        null=True
    )

    sirene_ftp_refresh_rate = models.PositiveIntegerField(
        verbose_name=(
            "Nombre de secondes entre deux mises "
            "à jour des données SIRENE"
        ),
        default=10,
        validators=[
            MinValueValidator(1)
        ]
    )

    hn_ip_address = models.GenericIPAddressField(
        protocol='IPv4',
        verbose_name="Adresse IP du server HN",
        blank=True,
        null=True
    )

    hn_port = models.PositiveIntegerField(
        verbose_name="Port du serveur HN",
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1)
        ]
    )

    hn_username = models.CharField(
        verbose_name="Login du serveur NH",
        max_length=128,
        blank=True,
        null=True
    )

    hn_password = models.CharField(
        verbose_name="Mot de passe du serveur NH",
        max_length=128,
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        """ Make sure only one settings is active at one time """
        with transaction.atomic():

            if self.active:
                Settings.objects.all().update(active=False)

            return super().save(*args, *kwargs)

    def __str__(self):
        return self.name
