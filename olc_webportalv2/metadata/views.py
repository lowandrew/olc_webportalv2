from django.shortcuts import render, get_object_or_404
from olc_webportalv2.metadata.forms import MetaDataRequestForm
from olc_webportalv2.metadata.models import MetaDataRequest


# Create your views here.
def metadata_home(request):
    form = MetaDataRequestForm()
    if request.method == 'POST':
        form = MetaDataRequestForm(request.POST)
    return render(request,
                  'metadata/metadata_home.html',
                  {
                     'form': form
                  })


def metadata_results(request, metadata_request_pk):
    metadata_result = get_object_or_404(MetaDataRequest, pk=metadata_request_pk)
    return render(request,
                  'metadata/metadata_results.html',
                  {
                      'metadata_result': metadata_result
                  })
