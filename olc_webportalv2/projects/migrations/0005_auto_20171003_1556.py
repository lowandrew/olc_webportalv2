# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-03 19:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_auto_20171003_1447'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='genesippr_results',
        ),
        migrations.AddField(
            model_name='project',
            name='genesippr_status',
            field=models.CharField(default='Unprocessed', max_length=128),
        ),
    ]