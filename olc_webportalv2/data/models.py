from django.db import models
from django.contrib.postgres.fields import ArrayField


# Create your models here.
class DataRequest(models.Model):
    seqids = ArrayField(models.CharField(max_length=24), blank=True, default=[])
    missing_seqids = ArrayField(models.CharField(max_length=24), blank=True, default=[])
    status = models.CharField(max_length=64, default='Unprocessed')
    download_link = models.CharField(max_length=256, blank=True)
