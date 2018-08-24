from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from olc_webportalv2.data.tasks import get_assembled_data
from olc_webportalv2.data.forms import DataRequestForm
from olc_webportalv2.data.models import DataRequest


# Create your views here.
@login_required
def data_home(request):
    return render(request,
                  'data/data_home.html',
                  {

                  })


@login_required
def assembled_data(request):
    form = DataRequestForm()
    if request.method == 'POST':
        form = DataRequestForm(request.POST)
        if form.is_valid():
            seqid_input = form.cleaned_data.get('seqids')
            seqids = seqid_input.split()
            data_request = DataRequest.objects.create(seqids=seqids)
            data_request.status = 'Processing'
            data_request.save()
            get_assembled_data(data_request_pk=data_request.pk)
            return redirect('data:assembled_data_download', data_request_pk=data_request.pk)
    return render(request,
                  'data/assembled_data.html',
                  {
                      'form': form
                  })


@login_required
def assembled_data_download(request, data_request_pk):
    data_request = get_object_or_404(DataRequest, pk=data_request_pk)
    return render(request,
                  'data/assembled_data_download.html',
                  {
                      'data_request': data_request
                  })


@login_required
def raw_data(request):
    return render(request,
                  'data/raw_data.html')
