from django.shortcuts import render, redirect
from olc_webportalv2.cowbat.forms import RunNameForm
from olc_webportalv2.cowbat.models import SequencingRun
from django.contrib.auth.decorators import login_required
import logging

log = logging.getLogger(__name__)


# Create your views here.
@login_required
def cowbat_home(request):
    form = RunNameForm()
    if request.method == 'POST':
        log.debug(request.FILES)
        form = RunNameForm(request.POST)
        if form.is_valid():
            log.debug('VALID FORM')
            files = [request.FILES.get('file[%d]' % i) for i in range(0, len(request.FILES))]
            for item in files:
                log.debug(item.name)
            return render(request,
                          'cowbat/cowbat_processing.html')
        else:
            log.debug('INVALID FORM')
    else:
        log.debug('NOT A POST REQUEST')
    return render(request,
                  'cowbat/cowbat_home.html',
                  {
                      'form': form,
                  })


@login_required
def cowbat_processing(request):
    return render(request,
                  'cowbat/cowbat_processing.html')
