from django.db import models
from multiselectfield import MultiSelectField
from olc_webportalv2.users.models import User

import datetime
import os


# Create your models here.


class Project(models.Model):
    """
    Main model for storing projects. Each project has a unique ID which is linked to a specific user.
    Job choices must be updated with new modules as they are implemented.
    I probably need to rethink the 'genesippr_status' column to support other tasks (i.e. FastQC).
    """
    JOB_CHOICES = (
        ('genesipprv2','GENESIPPRV2'),
        ('fastqc', 'FASTQC')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_title = models.CharField(max_length=256)
    description = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    file_R1 = models.FileField(upload_to='', blank=True)
    file_R2 = models.FileField(upload_to='', blank=True)
    organism = models.CharField(max_length=256,
                                blank=True)
    reference = models.CharField(max_length=256,
                                 blank=True)
    type = models.CharField(max_length=128,
                            blank=True)
    genesippr_status = models.CharField(max_length=128,
                                         default="Unprocessed")
    requested_jobs = MultiSelectField(choices=JOB_CHOICES)

    def filename_r1(self):
        return os.path.basename(self.file_R1.name)

    def filename_r2(self):
        return os.path.basename(self.file_R2.name)

    # This mess is necessary in order to pre-save the PK for use in the final file path for uploaded files.
    def save(self, *args, **kwargs):
        super(Project, self).save(*args, **kwargs)

        file_R1 = self.file_R1
        file_R2 = self.file_R2

        if file_R1 and file_R2:
            old_R1, old_R2 = self.file_R1.name, self.file_R2.name
            new_R1 = '/'.join(['uploads', self.user.username, datetime.datetime.now().strftime("%Y_%m_%d"),
                               str(self.pk),
                               str(self.file_R1.name)])
            new_R2 = '/'.join(['uploads', self.user.username, datetime.datetime.now().strftime("%Y_%m_%d"),
                               str(self.pk),
                               str(self.file_R2.name)])

            if new_R1 != old_R1 and new_R2 != old_R2:
                self.file_R1.storage.delete(new_R1)
                self.file_R1.storage.save(new_R1, file_R1)
                self.file_R1.name = new_R1
                self.file_R1.close()
                self.file_R1.storage.delete(old_R1)

                self.file_R2.storage.delete(new_R2)
                self.file_R2.storage.save(new_R2, file_R2)
                self.file_R2.name = new_R2
                self.file_R2.close()
                self.file_R2.storage.delete(old_R2)

        super(Project, self).save(*args, **kwargs)


class GenesipprResults(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    strain = models.CharField(max_length=256, default="N/A")
    genus = models.CharField(max_length=256, default="N/A")


#  Deleting the following functions results in an irritating migration error. Should probably fix this one day...
def generate_path():
    pass


def make_path(instance, filename):
    pass
