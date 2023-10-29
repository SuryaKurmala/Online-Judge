from django.contrib import admin
from .models import Problem, TestCase
from django.contrib.auth.models import User

admin.site.register(Problem)
admin.site.register(TestCase)