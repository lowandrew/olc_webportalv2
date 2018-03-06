from django.contrib import admin
from .models import ProjectMulti, Sample, SendsketchResult

# Register your models here.
admin.site.register(ProjectMulti)
admin.site.register(Sample)
admin.site.register(SendsketchResult)
