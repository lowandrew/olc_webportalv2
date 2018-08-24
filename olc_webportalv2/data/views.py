from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def data_home(request):
    return render(request,
                  'data/data_home.html',
                  {

                  })


@login_required
def assembled_data(request):
    return render(request,
                  'data/assembled_data.html')


@login_required
def raw_data(request):
    return render(request,
                  'data/raw_data.html')
