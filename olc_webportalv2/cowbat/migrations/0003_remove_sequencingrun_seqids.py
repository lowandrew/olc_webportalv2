# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-07-04 19:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cowbat', '0002_auto_20180704_1956'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sequencingrun',
            name='seqids',
        ),
    ]