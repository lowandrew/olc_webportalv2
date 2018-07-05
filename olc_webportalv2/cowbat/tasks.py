from background_task import background
from olc_webportalv2.cowbat.models import SequencingRun
from subprocess import check_output
import shutil
import os


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
    # TODO: Upload results to blob storage and then get rid of everything except for reports and storage.
