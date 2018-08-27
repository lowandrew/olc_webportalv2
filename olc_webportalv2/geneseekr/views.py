from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from olc_webportalv2.geneseekr.forms import GeneSeekrForm
from olc_webportalv2.geneseekr.models import GeneSeekrRequest
from olc_webportalv2.geneseekr.tasks import run_geneseekr

import datetime

# Create your views here.
@login_required
def geneseekr_home(request):
    one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
    geneseekr_requests = GeneSeekrRequest.objects.filter(user=request.user).filter(created_at__gte=one_week_ago)
    return render(request,
                  'geneseekr/geneseekr_home.html',
                  {
                      'geneseekr_requests': geneseekr_requests
                  })


@login_required
def geneseekr_query(request):
    form = GeneSeekrForm()
    if request.method == 'POST':
        form = GeneSeekrForm(request.POST, request.FILES)
        if form.is_valid():
            seqid_input = form.cleaned_data.get('seqids')
            seqids = seqid_input.split()
            geneseekr_request = GeneSeekrRequest.objects.create(user=request.user,
                                                                seqids=seqids)
            # Use query sequence if entered. Otherwise, read in the FASTA file provided.
            if form.cleaned_data.get('query_sequence') != '':
                geneseekr_request.query_sequence = form.cleaned_data.get('query_sequence')
            else:
                input_sequence_file = request.FILES['query_file']
                # Pointer is at end of file in request, so move back to beginning before doing the read.
                input_sequence_file.seek(0)
                input_sequence = input_sequence_file.read()
                geneseekr_request.query_sequence = input_sequence
            geneseekr_request.status = 'Processing'
            geneseekr_request.save()
            run_geneseekr(geneseekr_request_pk=geneseekr_request.pk)
            return redirect('geneseekr:geneseekr_processing', geneseekr_request_pk=geneseekr_request.pk)
    return render(request,
                  'geneseekr/geneseekr_query.html',
                  {
                     'form': form
                  })


@login_required
def geneseekr_processing(request, geneseekr_request_pk):
    geneseekr_request = get_object_or_404(GeneSeekrRequest, pk=geneseekr_request_pk)
    return render(request,
                  'geneseekr/geneseekr_processing.html',
                  {
                     'geneseekr_request': geneseekr_request
                  })
