from django import forms
from django.forms import ModelForm
from User.models import Submission

class CodeForm(ModelForm):
    class Meta:
        model = Submission
        fields = ['user_code']
        widgets = {'user_code' : forms.Textarea()}