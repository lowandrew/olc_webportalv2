from django.shortcuts import render
from olc_webportalv2.cowbat.forms import FileForm
from olc_webportalv2.cowbat.models import SequencingRun
from django.contrib.auth.decorators import login_required
import logging

log = logging.getLogger(__name__)


# Create your views here.
def cowbat_home(request):
    if request.method == 'POST':
        log.info('asdfasdfasdfasfa')
        log.info(request.FILES)
        files = request.FILES.getlist('file')
        for item in files:
            if item.name == 'SampleSheet.csv':
                instance = SequencingRun(samplesheet=item)
                instance.save()
    else:
        log.info('asdfasdfa')
    return render(request,
                  'cowbat/cowbat_home.html')
