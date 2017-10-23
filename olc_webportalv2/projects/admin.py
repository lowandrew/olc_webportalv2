from django.contrib import admin
from .models import Project, GenesipprResults, SendsketchResults


# Register your models here.
admin.site.register(Project)
admin.site.register(GenesipprResults)
admin.site.register(SendsketchResults)
