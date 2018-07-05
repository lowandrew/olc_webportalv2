# Django-related imports
from django.core.mail import send_mail  # To be used eventually, only works in cloud
from background_task import background
from olc_webportalv2.cowbat.models import SequencingRun
from django.conf import settings  # To access azure credentials
# Standard python stuff
from subprocess import check_output
import shutil
import glob
import os
# Other (azure related)
from azure.storage.blob import BlockBlobService


@background(schedule=1)
def run_cowbat(sequencing_run_pk):
    sequencing_run = SequencingRun.objects.get(pk=sequencing_run_pk)
    # Run COWBAT container - cowbat image is made with user as ubuntu, which causes permission issues
    # when files are uploaded. Hopefully setting user to root fixes that.
    cmd = 'docker exec -u root:root ' \
          'olcwebportalv2_cowbat ' \
          '/bin/bash -c "source activate cowbat && assembly_pipeline.py -s /sequences/{run_name} ' \
          '-r /mnt/nas2/databases/assemblydatabases/0.3.2"'.format(run_name=str(sequencing_run))
    try:
        p = check_output(cmd, shell=True)
    except:
        SequencingRun.objects.filter(pk=sequencing_run_pk).update(status='Error')
        return

    # With the sequencing run done, need to put create a zipfile with assemblies and reports for user to download.
    # First create a folder.
    os.makedirs('olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run)))
    # Now copy the reports and assemblies to the created folder.
    cmd = 'cp -r {best_assemblies} ' \
          '{download_folder}'.format(best_assemblies='olc_webportalv2/media/{run_name}/BestAssemblies'.format(run_name=str(sequencing_run)),
                                     download_folder='olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run)))
    os.system(cmd)
    cmd = 'cp -r {reports} ' \
          '{download_folder}'.format(reports='olc_webportalv2/media/{run_name}/reports'.format(run_name=str(sequencing_run)),
                                     download_folder='olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run)))
    os.system(cmd)

    # With that done, create a zipfile.
    shutil.make_archive('olc_webportalv2/media/{run_name}/{run_name}'.format(run_name=str(sequencing_run)),
                        'zip', 'olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run)))

    # We should now have a file in /sequences/run_name called run_name.zip - this is what we'll upload.

    SequencingRun.objects.filter(pk=sequencing_run_pk).update(status='Complete')

    # Upload results to blob storage and then get rid of everything except for reports and storage.
    # Blobs don't like folders, so create a zip folder out of the whole run.
    shutil.make_archive('olc_webportalv2/media/{run_name}'.format(run_name=str(sequencing_run)),
                        'zip',
                        'olc_webportalv2/media/{run_name}'.format(run_name=str(sequencing_run)))
    # Now login to blob service and upload ye olde zip file as blob to container.
    # Make the container with _ replaced with - and all lower case.
    container_name = str(sequencing_run).replace('_', '-').lower()
    blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                    account_key=settings.AZURE_ACCOUNT_KEY)
    blob_service.create_container(container_name)
    blob_service.create_blob_from_path(container_name, str(sequencing_run) + '.zip',
                                       'olc_webportalv2/media/{run_name}.zip'.format(run_name=str(sequencing_run)))
    os.remove('olc_webportalv2/media/{run_name}.zip'.format(run_name=str(sequencing_run)))

    # Finally, to save space on storage, get rid of everything except for the reports/assemblies zipfile
    # in the run folder, since we've gotten everything uploaded to blob land.
    files_in_run_folder = glob.glob('olc_webportalv2/media/{run_name}'.format(run_name=str(sequencing_run)))
    for item in files_in_run_folder:
        if not item.endswith('.zip'):
            if os.path.isfile(item):
                shutil.rmtree(item)
            elif os.path.isfile(item):
                os.remove(item)
    # Finally (but actually this time) send an email to relevant people to let them know that things have worked.
    # Uncomment this on the cloud where email sending actually works
    """
    send_mail(subject='TEST PLEASE IGNORE - Run {} has finished assembly.'.format(str(sequencing_run)),
              message='If you are Andrew or Adam, please download blob container {} to local OLC storage.'
                      ' If you\'re Paul, please add this data to the OLC database.'.format(container_name),
              from_email='olcbioinformatics@gmail.com',
              recipient_list=['paul.manninger@canada.ca', 'andrew.low@canada.ca', 'adam.koziol@canada.ca'])
    """
