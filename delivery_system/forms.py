from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from material import Layout, Row
from .models import DeliveryTask, StateDeliveryTask, Staff


class LoginForm(AuthenticationForm):
    layout = Layout('username',
                    Row('password'))


class AddDeliveryTaskForm(forms.ModelForm):

    layout = Layout('title_name',
                    'priority')
    priority = forms.ChoiceField(widget=forms.RadioSelect, choices=DeliveryTask.PRIORITIES)

    class Meta:
        model = DeliveryTask
        fields = ('title_name',)

    def clean(self):
        # print(self.request)
        if DeliveryTask.objects.filter(created_by=User.objects.get(username=self.data['username']),title_name__iexact=self.cleaned_data['title_name']):
            self.add_error('title_name', "You already a created a task with this name")
        return self.cleaned_data
