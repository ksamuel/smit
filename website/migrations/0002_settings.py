# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-23 00:11
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('active', models.BooleanField(default=True, verbose_name='Activer cette configuration')),
                ('sirene_ftp_ip_address', models.GenericIPAddressField(blank=True, null=True, protocol='IPv4', verbose_name='Adresse IP du FTP SIRENE')),
                ('sirene_ftp_port', models.PositiveIntegerField(blank=True, default=21, null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Port du FTP SIRENE')),
                ('sirene_ftp_username', models.CharField(blank=True, max_length=128, null=True, verbose_name='Login du FTP SIRENE')),
                ('sirene_ftp_password', models.CharField(blank=True, max_length=128, null=True, verbose_name='Mot de passe du FTP SIRENE')),
                ('sirene_csv_file_path', models.CharField(blank=True, default='VTM_ATTENDUS_PILOTAGE_V2.csv', max_length=512, null=True, verbose_name='Chemin du fichier CSV de SIRENE')),
                ('sirene_ftp_refresh_rate', models.PositiveIntegerField(default=10, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Nombre de secondes entre deux mises à jour des données SIRENE.')),
                ('hn_ip_address', models.GenericIPAddressField(blank=True, null=True, protocol='IPv4', verbose_name='Adresse IP du server HN')),
                ('hn_port', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Port du serveur HN')),
                ('hn_username', models.CharField(blank=True, max_length=128, null=True, verbose_name='Login du serveur NH')),
                ('hn_password', models.CharField(blank=True, max_length=128, null=True, verbose_name='Mot de passe du serveur NH')),
            ],
            options={
                'verbose_name': 'Configuration',
            },
        ),
    ]