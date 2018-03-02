# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-19 17:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cfia_access',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='lab',
            field=models.CharField(blank=True, choices=[(1, 'St-Johns'), (2, 'Dartmouth'), (3, 'Charlottetown'), (4, 'St-Hyacinthe'), (5, 'Longeuil'), (6, 'Fallowfield'), (7, 'Carling'), (8, 'Greater Toronto Area'), (9, 'Winnipeg'), (10, 'Saskatoon'), (11, 'Calgary'), (12, 'Lethbridge'), (13, 'Burnaby'), (14, 'Sidney'), (15, 'Other')], max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='rank',
            field=models.CharField(choices=[('Diagnostic', 'Diagnostic'), ('Research', 'Research'), ('Manager', 'Manager'), ('Quality', 'Quality'), ('Super', 'Super')], default='Diagnostic', max_length=100),
        ),
    ]