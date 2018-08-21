from django.core.management.base import BaseCommand
from olc_webportalv2.cowbat.models import AzureTask, SequencingRun
from django.core.mail import send_mail  # To be used eventually, only works in cloud
from django.conf import settings
from olc_webportalv2.cowbat.tasks import cowbat_cleanup
import time
import os


def monitor_tasks():
    while True:
        azure_tasks = AzureTask.objects.filter()
        for task in azure_tasks:
            if os.path.isfile(task.exit_code_file):
                sequencing_run = SequencingRun.objects.get(pk=task.sequencing_run.pk)
                # Read exit code. Update status to 'Error' if non-zero, 'Completed' if zero.
                # Run any tasks necessary to clean things up/have reports run.
                with open(task.exit_code_file) as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.rstrip()
                    if int(line.split(',')[1]) != 0:
                        SequencingRun.objects.filter(pk=sequencing_run.pk).update(status='Error')
                        """
                        send_mail(subject='Assembly Error - Run {} was successfully submitted Azure Batch, but did not complete assembly'.format(str(sequencing_run)),
                                  message='Fix it!',
                                  from_email=settings.EMAIL_HOST_USER,
                                  recipient_list=['andrew.low@canada.ca'])
                        """
                    else:
                        cowbat_cleanup(sequencing_run_pk=sequencing_run.pk)  # This also sets task to complete
                        # Delete task so we don't have to keep checking up on it.
                        AzureTask.objects.filter(id=task.id).delete()

        time.sleep(30)


class Command(BaseCommand):
    help = 'Command to monitor cowbat tasks that have been submitted to azure batch'

    def handle(self, *args, **options):
        monitor_tasks()
