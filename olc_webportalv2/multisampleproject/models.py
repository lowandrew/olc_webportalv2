from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField
from olc_webportalv2.users.models import User

import datetime
import glob
import os


def validate_fastq(fieldfile):
    filename = os.path.basename(fieldfile.name)
    if filename.endswith('.fastq.gz') or filename.endswith('.fastq'):
        print('File extension for {} confirmed valid'.format(filename))
    else:
        raise ValidationError(
            _('%(file)s does not end with .fastq or .fastq.gz'),
            params={'filename': filename},
        )


def find_paired_reads(fastq_directory, forward_id='_R1', reverse_id='_R2'):
    """
    Looks at a directory to try to find paired fastq files. Should be able to find anything fastq.
    :param fastq_directory: Complete path to directory containing fastq files.
    :param forward_id: Identifier for forward reads. Default R1.
    :param reverse_id: Identifier for reverse reads. Default R2.
    :return: List containing pairs of fastq files, in format [[forward_1, reverse_1], [forward_2, reverse_2]], etc.
    """
    pair_list = list()
    fastq_files = glob.glob(os.path.join(fastq_directory, '*.f*q*'))
    for name in fastq_files:
        if forward_id in name and os.path.isfile(name.replace(forward_id, reverse_id)):
            pair_list.append([name, name.replace(forward_id, reverse_id)])
    return pair_list


def retrieve_sampleid(paired_reads, forward_id='_R1', reverse_id='_R2'):
    """
    :param paired_reads: List containing R1 and R2 filenames i.e. [R1, R2]
    :return: tries to estimate the common sample ID and returns its name
    """
    read_1 = paired_reads[0]
    read_2 = paired_reads[1]

    r1_id = read_1.split(forward_id)[0]
    r2_id = read_2.split(reverse_id)[0]

    if r1_id == r2_id:
        return r1_id
    else:
        return 'SampleID mismatch between {} and {}'.format(read_1, read_2)

class MultiProject(models.Model):
    """
    Main model for storing projects. Each project has a unique ID which is linked to a specific user.
    Job choices must be updated with new modules as they are implemented.
    """
    JOB_CHOICES = (
        ('genesipprv2', 'GenesipprV2'),
        ('sendsketch', 'sendsketch'),
    )

    # user key is pulled from the User model
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_title = models.CharField(max_length=256)
    description = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    sample_list = models.CharField(max_length=128, blank=True) # TODO: Make this a dict of files + sample IDs provided by user
    genesippr_status = models.CharField(max_length=128,
                                        default="Unprocessed")
    sendsketch_status = models.CharField(max_length=128,
                                         default="Unprocessed")
    requested_jobs = MultiSelectField(choices=JOB_CHOICES)

    def genesippr_report_path(self):
        return str(os.path.join(os.path.dirname(self.file_R1.name), 'reports/reports.zip'))

    def filename_r1(self):
        return os.path.basename(self.file_R1.name)

    def filename_r2(self):
        return os.path.basename(self.file_R2.name)

    def __str__(self):
        return '{}:{}'.format(self.user, str(self.pk))

    def save(self, *args, **kwargs):
        super(MultiProject, self).save(*args, **kwargs)

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

        super(MultiProject, self).save(*args, **kwargs)


class Samples(models.Model):
    def __str__(self):
        return '{}'.format(self.project)

    project = models.ForeignKey(MultiProject, on_delete=models.CASCADE)


