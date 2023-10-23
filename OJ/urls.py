from django.urls import path
from . import views

urlpatterns = [
    path('', views.problemPage, name='problems'),
    path('<int:problem_id>/', views.descriptionPage, name='description'),
    path('<int:problem_id>/verdict/', views.verdictPage, name='verdict'),
]
