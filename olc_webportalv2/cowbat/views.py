from django.shortcuts import render


# Create your views here.
def cowbat_home(request):
    return render(request,
                  'cowbat/cowbat_home.html')
