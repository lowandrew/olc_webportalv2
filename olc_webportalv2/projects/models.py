from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField
from olc_webportalv2.users.models import User

import datetime
import os


# Validation functions
def validate_fastq(fieldfile):
    filename = os.path.basename(fieldfile.name)
    if filename.endswith('.fastq.gz') or filename.endswith('.fastq'):
        print('File extension for {} confirmed valid'.format(filename))
    else:
        raise ValidationError(
            _('%(file)s does not end with .fastq or .fastq.gz'),
            params={'filename': filename},
        )

# Create your models here.


class Project(models.Model):
    """
    Main model for storing projects. Each project has a unique ID which is linked to a specific user.
    Job choices must be updated with new modules as they are implemented.
    I probably need to rethink the 'genesippr_status' column to support other tasks (i.e. FastQC).
    """
    JOB_CHOICES = (
        ('genesipprv2', 'GenesipprV2'),
        ('sendsketch', 'sendsketch'),
        ('gloobleshteen', 'Gloobleshteen'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_title = models.CharField(max_length=256)
    description = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    file_R1 = models.FileField(upload_to='', blank=True, validators=[validate_fastq])
    file_R2 = models.FileField(upload_to='', blank=True, validators=[validate_fastq])
    organism = models.CharField(max_length=256,
                                blank=True)
    reference = models.CharField(max_length=256,
                                 blank=True)
    type = models.CharField(max_length=128,
                            blank=True)
    genesippr_status = models.CharField(max_length=128,
                                        default="Unprocessed")
    sendsketch_status = models.CharField(max_length=128,
                                         default="Unprocessed")
    requested_jobs = MultiSelectField(choices=JOB_CHOICES)

    def filename_r1(self):
        return os.path.basename(self.file_R1.name)

    def filename_r2(self):
        return os.path.basename(self.file_R2.name)

    # For admin panel
    def __str__(self):
        return '{}:{}'.format(self.user,str(self.pk))

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
    # For admin panel
    def __str__(self):
        return '{}'.format(self.project)

    # TODO: Accomodate seqID
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    strain = models.CharField(max_length=256, default="N/A")
    genus = models.CharField(max_length=256, default="N/A")
    gdcs = models.CharField(max_length=256, default="N/A")
    gdcs_coverage = models.CharField(max_length=256, default="N/A")
    pass_fail = models.CharField(max_length=256, default="N/A")

    # # STEC fields
    # uida = models.CharField(max_length=256, default="N/A")
    # stx1 = models.CharField(max_length=256, default="N/A")
    # stx2 = models.CharField(max_length=256, default="N/A")
    # stx2f = models.CharField(max_length=256, default="N/A")
    # eae = models.CharField(max_length=256, default="N/A")
    # serotype = models.CharField(max_length=256, default="N/A")
    #
    # # Salmonella fields
    # inva = models.CharField(max_length=256, default="N/A")
    # stn = models.CharField(max_length=256, default="N/A")
    #
    # # Listeria fields
    # hyla = models.CharField(max_length=256, default="N/A")
    # inij = models.CharField(max_length=256, default="N/A")
    # igs = models.CharField(max_length=256, default="N/A")


class SendsketchResults(models.Model):
    # For admin panel
    def __str__(self):
        return '{}'.format(self.project)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)


#  Deleting the following functions results in an irritating migration error. Should probably fix this one day...
def generate_path():
    pass


def make_path(instance, filename):
    pass
