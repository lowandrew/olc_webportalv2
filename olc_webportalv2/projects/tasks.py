from subprocess import Popen
from background_task import background
from .models import Project, GenesipprResults
import glob
import csv


@background(schedule=5)
def run_genesippr(file_path, proj_pk):

    # Set genesippr status
    Project.objects.filter(id=proj_pk).update(genesippr_status="Processing...")

    print('\nrun_genesippr() called successfully for project ID {}'.format(proj_pk))

    # Run Genesippr
    cmd = 'docker exec ' \
          'genesipprv2 ' \
          'python3 ' \
          'geneSipprV2/sipprverse/method.py ' \
          '/sequences/{0} ' \
          '-t /targets ' \
          '-s /sequences/{0}'.format(file_path)

    p = Popen(cmd, shell=True)
    p.communicate()  # wait until the script completes before resuming the code

    print('\nGenesipprV2 container actions complete')

    genesippr_result_path = glob.glob('olc_webportalv2/media/{}/reports/genesippr.csv'.format(file_path))
    genesippr_result_path = genesippr_result_path[0]

    print('\nAttempting to read ' + genesippr_result_path)
    try:
        read_genesippr_results(genesippr_result_path, proj_pk)
        Project.objects.filter(pk=proj_pk).update(genesippr_status="Complete")
        print('\nReading genesippr results complete.')
    except:
        print('\nReading genesippr results failed.')


def add_genesippr_csv_result(proj_pk, strain, genus,):
    """
    Function to retrieve a specific project ID, then update the GenesipprResults model with according data from
    the genesippr.csv report created.
    """
    c = GenesipprResults.objects.filter(project=Project.objects.get(id=proj_pk)).update(strain=strain,
                                                                                        genus=genus,)
    return c


def read_genesippr_results(genesippr_result_path, proj_pk):
    with open(genesippr_result_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        # header = next(reader)
        for row in reader:
            add_genesippr_csv_result(proj_pk=proj_pk,
                                     strain=str(row[0]),
                                     genus=str(row[1]),
                                     )
