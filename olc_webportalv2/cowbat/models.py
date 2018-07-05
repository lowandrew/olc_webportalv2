from django.db import models
from django.contrib.postgres.fields import ArrayField
import os

# Create your models here.


def get_run_name(instance, filename):
    return os.path.join(instance.sequencing_run.run_name, filename)


def get_interop_name(instance, filename):
    return os.path.join(instance.sequencing_run.run_name, 'InterOp', filename)


class SequencingRun(models.Model):
    run_name = models.CharField(max_length=64)
    status = models.CharField(max_length=64, default='Unprocessed')
    seqids = ArrayField(models.CharField(max_length=24), blank=True, default=[])

    def __str__(self):
        return self.run_name


class DataFile(models.Model):
    sequencing_run = models.ForeignKey(SequencingRun, on_delete=models.CASCADE, related_name='datafile')
    data_file = models.FileField(upload_to=get_run_name)


class InterOpFile(models.Model):
    sequencing_run = models.ForeignKey(SequencingRun, on_delete=models.CASCADE, related_name='interop')
    interop_file = models.FileField(upload_to=get_interop_name)
