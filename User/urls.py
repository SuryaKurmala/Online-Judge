# urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutPage, name='logout'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('password-change-done/', views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('all_submissions/', views.allSubmissionPage, name='all_submissions'),
    path('account/', views.account, name='account'),
]
