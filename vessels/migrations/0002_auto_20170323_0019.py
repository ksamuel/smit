# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-23 00:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vessels', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vessel',
            options={'verbose_name': 'Navire'},
        ),
        migrations.AlterField(
            model_name='vessel',
            name='call_sign',
            field=models.CharField(max_length=16),
        ),
    ]