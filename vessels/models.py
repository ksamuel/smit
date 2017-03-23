
import uuid

import pendulum

from haversine import haversine

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.forms.models import model_to_dict

from django_extensions.db.models import TimeStampedModel

from .utils import Coordinates


class BaseModel(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Vessel(BaseModel):

    class Meta:
        verbose_name = "Navire"

    HELICO_CHOICES = (
        ('yes', 'Oui'),
        ('no', 'Non'),
        ('quiet_sea_only', 'PMC')  # french for "Pilotage Mer Calme"
    )

    # source: SIRENE's "NOMNAVIRE" field
    name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )
    # Source: SIRENE's "CALLSIGN" field
    call_sign = models.CharField(
        max_length=16,
    )
    # Source: SIRENE's "LONGUEUR" field. Unit to be confirmed.
    length = models.FloatField(
        validators=[MinValueValidator(0.1)],
        null=True,
        blank=True,
        verbose_name="L"
    )
    # Source: SIRENE's "TIRANTEAU" field. Unit to be confirmed.
    draft = models.FloatField(
        validators=[MinValueValidator(0.1)],
        null=True,
        blank=True,
        verbose_name="TE"
    )

    # source: pilot input
    helico_observation = models.TextField(
        null=True,
        blank=True,
        verbose_name="Obs hélico"
    )

    # Source: Pilot input
    helico = models.CharField(
        choices=HELICO_CHOICES,
        null=True,
        blank=True,
        max_length=32,
    )

    def __repr__(self):
        return (f'Vessel(call_sign={self.call_sign!r}, name={self.name!r}, '
                f'length={self.length!r}, draft={self.draft!r})')

    def __str__(self):
        return f'Vessel [{self.call_sign}] "{self.name}"'

    def get_latest_activity(self, new_activity_delay=5 * 3600):
        """ Return last matching activity for this vessel or a new one """

        lastest_activity = (VesselActivity.objects
                                          .filter(vessel=self)
                                          .order_by('-modified')
                                          .first())

        if lastest_activity:

            if lastest_activity.type != 'departing':
                return lastest_activity

            now = pendulum.utcnow()
            oldest_accepted_date = now.add(seconds=-new_activity_delay)

            if lastest_activity.modified > oldest_accepted_date:
                return lastest_activity

        return None

    def to_dict(self):
        return model_to_dict(self)


class VesselActivity(BaseModel):

    ROUTE_CHOICES = ((x, str(x)) for x in range(1, 16))

    TYPE_CHOICES = (
        ('incomming', 'E'),  # french for "Entrée"
        ('departing', 'S'),  # french for "Sortie"
        ('shifting', 'D')  # french for "Déhalage"
    )
    STATUS_CHOICES = (
        ('piloting', 'Piloter'),
        ('anchoring', 'Mouiller'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    vessel = models.ForeignKey(Vessel)

    # source: SIRENE's "MOUVEMENT" field
    type = models.CharField(
        max_length=16,
        choices=TYPE_CHOICES,
        null=True,
        blank=True
    )

    # source: operator input
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        null=True,
        blank=True
    )

    # source: SIRENE's "BONPOURMOUVEMENT" field
    good_to_go = models.BooleanField(
        default=False,
        verbose_name="BPV"  # french for "Bon Pour Mouvement"
    )

    # Source: SIRENE's "PROVENANCE" field
    incoming_from = models.CharField(max_length=128, null=True, blank=True)

    # Source: SIRENE's "DESTINATION" field
    leaving_to = models.CharField(max_length=128, null=True, blank=True)

    # Source: SIRENE's "POSTEAQUAI" field
    berth = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name="PaQ"  # french for "Poste à Quai"
    )

    # Source: Operator input
    # Currently unused. Keeping in case the client changes his mind.
    route = models.IntegerField(
        choices=ROUTE_CHOICES,
        null=True,
        blank=True,
        verbose_name="RTE"
    )

    # Source: sirene's "DATEDEBUTMVTPREVUE" field. timezone to be confirmed.
    sirene_time_estimate = models.DateTimeField(
        null=True,
        blank=True
    )

    # source: sirene's "OBSERVATIONS"
    sirene_observation = models.TextField(
        null=True,
        blank=True,
        verbose_name="Obs SIRENE"
    )

    # source: NAVY HARBOR xml data from
    # <ns:TrackData TrackStatus ...><ns:Pos Long="14.501566" Lat="35.880936"/>
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)

    # source: sirene's "NOMBREDETUGS"
    tugs = models.IntegerField(
        null=True,
        blank=True,
    )

    # source: sirene's "DEBUTDESOPERATIONSCOMMERCIALES"
    services = models.TextField(
        null=True,
        blank=True,
        verbose_name="OP commerciale"
    )

    # source: sirene's "NAVIREDANGEREUX"
    dangerous_materials = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Dgx"
    )

    @classmethod
    def get_recent_activity_for(cls, name, new_activity_delay=5 * 3600):
        """ Return a recent activity a vessel of this name """

        now = pendulum.utcnow()
        oldest_accepted_date = now.add(seconds=-new_activity_delay)

        try:
            return cls.objects.get(
                vessel__name=name,
                modified__gt=oldest_accepted_date
            )
        except (
            cls.DoesNotExist,
            cls.MultipleObjectsReturned
        ):
            return None

    @property
    def coordinates(self):
        return Coordinates(self.latitude, self.longitude)

    # AKA: ZV
    @property
    def distance_to_red_dot(self):
        if not self.longitude or self.latitude:
            raise ValueError(
                'Cannot calculate distance to red dot '
                'without longitude and latitude'
            )

        return haversine((self.latitude, self.longitude), settings.RED_DOT)

    def to_dict(self, timezone='UTC', include_vessel=False):

        if include_vessel:
            vessel_activity_dict = self.vessel.to_dict()
            vessel_activity_dict.update(model_to_dict(self))
        else:
            vessel_activity_dict = model_to_dict(self)

        # cast uuid to strings
        vessel_activity_dict['id'] = str(vessel_activity_dict['id'])
        vessel_activity_dict['vessel'] = str(vessel_activity_dict['vessel'])

        # cast date to string
        time = vessel_activity_dict['sirene_time_estimate']
        if time:
            now = pendulum.now().in_timezone(timezone)
            # ensure we always have a pendulum object and convert
            # to local timezone
            time = pendulum.instance(time).in_timezone(timezone)
            if now.day == time.day:
                time = f'{time:%H:%M}'
            else:
                time = f'{time:%d/%m/%y %H:%M}'
        vessel_activity_dict['sirene_time_estimate'] = time

        return vessel_activity_dict
