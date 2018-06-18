from django.db import models

# Create your models here.


class SequencingRun(models.Model):
    samplesheet = models.FileField(upload_to='test', blank=True)
