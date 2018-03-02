from django.shortcuts import render, get_object_or_404
import os

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig
from .models import ProjectMulti, Attachment
from .forms import ProjectForm
# Create your views here.


@login_required
def new_multisample(request):
    project_list = ProjectMulti.objects.filter(user=request.user)
    form = ProjectForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            print('Form is valid.\n')

            # Have to do this in order to set the user to current logged in user
            new_entry = form.save(commit=False)

            # Pull active user
            new_entry.user = request.user

            # Save the form
            new_entry = form.save()

    return render(request,
                  'new_multisample/new_multisample.html',
                  {'project_list': project_list,
                   'form': form,
                   'project_id': ProjectMulti.pk,
                   'user': request.user
                   }
                  )

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(ProjectMulti, pk=project_id)
    # try:
    #     project_id = ProjectMulti.objects.get(pk=project_id)
    # except ProjectMulti.DoesNotExist:
    #     raise Http404("Project ID {} does not exist.".format(project_id))

    if request.method == 'POST':
        # form = SampleForm(request.POST)
        files = request.FILES.getlist('files')
        for item in files:
            instance = Attachment(attachment=item)
            instance.save()
        # if form.is_valid():
        #     form.save()
    # else:
    #     form = SampleForm()
    return render(request,
                  'new_multisample/project_detail.html',
                  {'project': project},  # 'form': form},
                  )
