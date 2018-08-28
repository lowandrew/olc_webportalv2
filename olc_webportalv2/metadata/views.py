from django.shortcuts import render, get_object_or_404, redirect
from olc_webportalv2.metadata.forms import MetaDataRequestForm
from olc_webportalv2.metadata.models import MetaDataRequest, SequenceData


# Create your views here.
def metadata_home(request):
    form = MetaDataRequestForm()
    if request.method == 'POST':
        form = MetaDataRequestForm(request.POST)
        if form.is_valid():
            quality = form.cleaned_data.get('quality')
            genus = form.cleaned_data.get('genus')
            # Logic on sequence requests.
            if quality == 'Fail':
                sequence_data_matching_query = SequenceData.objects.filter(genus__iexact=genus)
            elif quality == 'Pass':
                sequence_data_matching_query = SequenceData.objects.filter(genus__iexact=genus).exclude(quality='Fail')
            elif quality == 'Reference':
                sequence_data_matching_query = SequenceData.objects.filter(genus__iexact=genus).filter(quality='Reference')
            metadata_request = MetaDataRequest()
            for sequence_data in sequence_data_matching_query:
                metadata_request.seqids.append(sequence_data.seqid)
            metadata_request.save()
            return redirect('metadata:metadata_results', metadata_request_pk=metadata_request.pk)
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
