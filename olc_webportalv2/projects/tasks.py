from subprocess import Popen
from background_task import background
from .models import Project
import glob


@background(schedule=5)
def run_genesippr(file_path, proj_pk):

    print('\nrun_genesippr() called successfully for project ID {}'.format(proj_pk))

    cmd = 'docker exec ' \
          'genesipprv2 ' \
          'python3 ' \
          'geneSipprV2/sipprverse/method.py ' \
          '/sequences/{0} ' \
          '-t /targets ' \
          '-s /sequences/{0}'.format(file_path)

    try:
        p = Popen(cmd, shell=True)
        p.communicate()  # wait until the script completes before resuming the code
        print('\nGenesipprV2 job complete')

        report_files = glob.glob('olc_webportalv2/media/{}/reports/*'.format(file_path))

        # Then maybe read the CSV output
        #read_genesippr_results(file_path)

        # Update model with new status
        Project.objects.filter(pk=proj_pk).update(genesippr_status="Complete")

    except:
        print("Something broke")
        Project.objects.filter(pk=proj_pk).update(genesippr_status="Error")


def read_genesippr_results(file_path):
    pass
