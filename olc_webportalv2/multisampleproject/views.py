import os

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig

from .models import MultiProject

@login_required
def multisampleprojects(request):
    project_list = MultiProject.objects.filter(user=request.user)

    return render(request,
                  'multisampleprojects/multiprojects.html',
                  {
                      'multisampleprojects': project_list,
                  }
                  )
