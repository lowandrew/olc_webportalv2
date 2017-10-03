from django.shortcuts import render
from .tasks import run_genesippr


# Create your views here.
def jobs(request):
    return render(request, 'jobs/jobs.html', {})


def submit(request):
    print('\nSUBMIT FUNCTION CALLED\n')
    if request.method == 'POST':
        # run_genesippr('admin/2017_10_02_1506712253')
        # run_genesippr.now('admin/2017_10_02_1506972169')
        return render(request, 'jobs/jobs.html', {})

