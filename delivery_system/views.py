import json

from channels import Group
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core import serializers
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView, DetailView, TemplateView

from delivery_system import asysn_tasks
from delivery_system.models import Staff, DeliveryTask, StateDeliveryTask
from .forms import LoginForm, AddDeliveryTaskForm
from material.frontend.views import ListModelView
from .asysn_tasks import get_new_tasks

# Create your views here.


class Login(LoginView):
    template_name = 'delivery_system/registration/login.html'
    authentication_form = LoginForm


class Home(TemplateView):
    template_name = 'home.html'


#
class Logout(LogoutView):
    next_page = '/delivery/login'


class CheckAuthenticationUserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.staff_list.is_store_manager()


class CheckDeliveryBoy(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.staff_list.is_delivery_boy()


class AddDeliveryTaskView(LoginRequiredMixin, CheckAuthenticationUserMixin, CreateView):
    login_url = '/login/'
    template_name = 'Tasks/create_task.html'
    form_class = AddDeliveryTaskForm
    success_message = "Task Created Successfully"

    def form_valid(self, form):
        """
               If the form is valid, save the associated model.
               """
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.priority = form.cleaned_data['priority']
        # Need to create a transition state
        self.object.save()
        StateDeliveryTask.objects.create(state=StateDeliveryTask.NEW, delivery_tak=self.object,
                                         state_change_by=self.request.user).save()

        # Connect.
        ordered = get_new_tasks()
        if ordered:
            Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", [ordered]),"type": 'TYPE_TASKS'})})
        else:
            Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", []),"type": 'TYPE_TASKS'})})

        return HttpResponseRedirect(reverse('delivery_system:home'))

    def get_current_user(self):
        return self.request.user


class ListOfTasks(LoginRequiredMixin, CheckAuthenticationUserMixin, ListView):
    template_name = 'Tasks/task_list.html'
    model = DeliveryTask
    context_object_name = 'tasks_list'
    paginate_by = 5
    queryset = DeliveryTask.objects.all().order_by('-modified_on')


class DetailsOfTasks(LoginRequiredMixin, CheckAuthenticationUserMixin, DetailView):
    template_name = 'Tasks/task_details.html'
    model = DeliveryTask
    context_object_name = 'task_details'


class DeliveryBoyAcceptedTasks(LoginRequiredMixin, CheckDeliveryBoy, ListView):
    template_name = 'Tasks/accepted_task.html'
    model = StateDeliveryTask
    context_object_name = 'accepted_task'
    paginate_by = 5

    def get_queryset(self):
        queryset = StateDeliveryTask.objects.filter(state_change_by=self.request.user).filter(delivery_tak__current_state=StateDeliveryTask.ACCEPTED).all()
        return queryset


def cancel_task(request, page_number, id):
    # Can only be cancelled by the store manager who created it.

    if request.user.is_authenticated:
        try:
            task = DeliveryTask.objects.select_for_update().filter(id=id).filter(created_by=request.user).first()
            if task:
                if task.current_state == StateDeliveryTask.NEW:
                    task.current_state = StateDeliveryTask.CANCELLED
                    task.save()
                    # Create new transition state.
                    task_state = StateDeliveryTask.objects.create(delivery_tak=task, state=StateDeliveryTask.CANCELLED,
                                                                  state_change_by=request.user)
                    task_state.save()
                    ordered = get_new_tasks()
                    if ordered:
                        Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", [ordered]),"type": 'TYPE_TASKS'})})
                    else:
                        Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", []),"type": 'TYPE_TASKS'})})

                    return HttpResponseRedirect(reverse('delivery_system:tasks_list') + '?page=%s' % page_number)
                else:
                    raise ValueError("You can't cancel this task")

            else:
                raise ValueError("Task Can't be cancelled Reason 1. You do not created this task 2. Task with this ID is not "
                                 "available.")
        except Exception as e:
            raise ValueError("Transaction updating on the selected database row by some other user. Please try after sometime", e)
    else:
        return HttpResponseRedirect(reverse('login'))


def decline_task(request, page_number, id):
    # Can only be Decline by the delivery boy who accepted it.

    if request.user.is_authenticated:
        try:
            task = DeliveryTask.objects.select_for_update().filter(id=id).first()
            if task:
                task_state = StateDeliveryTask.objects.get(delivery_tak=task, state=StateDeliveryTask.ACCEPTED,
                                                           state_change_by=request.user)
                if task_state:
                    task.current_state = StateDeliveryTask.DECLINED
                    task.save()
                    # Create new transition state.
                    new_state = StateDeliveryTask.objects.create(delivery_tak=task, state=StateDeliveryTask.DECLINED,
                                                                 state_change_by=request.user)
                    new_state.save()
                    # Update Queue: Add task to queue
                    #  Real Time update user interface.
                    # ordered = get_new_tasks()
                    # if ordered:
                    #     Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", [ordered]),"type": 'TYPE_TASKS'})})
                    # else:
                    #     Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", []),"type": 'TYPE_TASKS'})})

                    # Alert Store Manager who created it.
                    Group('notification').send({"text": json.dumps({'data': str("Delivery boy - "+request.user.username+" declined your task "+task.title_name), "type": 'NOTIFY'})})
                    return HttpResponseRedirect(reverse('delivery_system:accepted_tasks') + '?page=%s' % page_number)
                else:
                    raise ValueError("Task does not specify condition 1. You are the not the deliver boy who Accepted this task")

            else:
                raise ValueError("Task Can't be cancelled Reason Task with this ID is not available.")
        except Exception as e:
            raise ValueError("Transaction updating on the selected database row by some other user.", e)
    else:
        return HttpResponseRedirect(reverse('login'))


def complete_task(request, page_number, id):
    if request.user.is_authenticated:
        try:
            task = DeliveryTask.objects.select_for_update().filter(id=id).first()
            if task:
                task_state = StateDeliveryTask.objects.get(delivery_tak=task, state=StateDeliveryTask.ACCEPTED,
                                                           state_change_by=request.user)
                if task_state:
                    task.current_state = StateDeliveryTask.COMPLETED
                    task.save()
                    # Create new transition state.
                    new_state = StateDeliveryTask.objects.create(delivery_tak=task, state=StateDeliveryTask.COMPLETED,
                                                                 state_change_by=request.user)
                    new_state.save()
                    # TODO: Real Time update user interface.
                    return HttpResponseRedirect(reverse('delivery_system:accepted_tasks')+ '?page=%s' % page_number)
                else:
                    raise ValueError("Task does not specify condition 1. You are the not the deliver boy who Accepted this task")

            else:
                raise ValueError("Task Can't be cancelled Reason Task with this ID is not available.")
        except Exception as e:
            raise ValueError("Transaction updating on the selected database row by some other user. Please try after sometime", e)
    else:
        return HttpResponseRedirect(reverse('login'))


def accept_task(request, id):
    if request.user.is_authenticated:
        # Check for more than 3 pending tasks
        query_set =StateDeliveryTask.objects.filter(state_change_by=request.user).filter(
            delivery_tak__current_state=StateDeliveryTask.ACCEPTED).all()
        if len(query_set) == 3:
            raise ValueError("You can't accept this task. Please complete your previous tasks!!")
        try:
            task = DeliveryTask.objects.select_for_update().filter(id=id).first()
            if task:
                task_state = StateDeliveryTask.objects.get(delivery_tak=task, state=StateDeliveryTask.NEW)
                if task_state:
                    task.current_state = StateDeliveryTask.ACCEPTED
                    task.save()
                    # Create new transition state.
                    new_state = StateDeliveryTask.objects.create(delivery_tak=task, state=StateDeliveryTask.ACCEPTED,
                                                                 state_change_by=request.user)
                    new_state.save()
                    ordered = get_new_tasks()
                    if ordered:
                        Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", [ordered]),"type": 'TYPE_TASKS'})})
                    else:
                        Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", []),"type": 'TYPE_TASKS'})})

                    # TODO: Not more than 3 tasks should be accepted.
                    return HttpResponseRedirect(reverse('delivery_system:accepted_tasks'))
                else:
                    raise ValueError("Task does not specify condition 1. State task is already picked or cancelled by manager.")

            else:
                raise ValueError("Task Can't be cancelled Reason Task with this ID is not available.")
        except Exception as e:
            raise ValueError("Transaction updating on the selected database row by some other user.", e)
    else:
        return HttpResponseRedirect(reverse('login'))

class AcceptATask(TemplateView):
    template_name = 'Tasks/accept_task.html'


class CompletedTaskView(LoginRequiredMixin, CheckDeliveryBoy,ListView):
    template_name = 'Tasks/completed_task.html'
    model = StateDeliveryTask
    context_object_name = 'completed_task'
    paginate_by = 5

    def get_queryset(self):
        queryset = StateDeliveryTask.objects.filter(state_change_by=self.request.user).filter(state=StateDeliveryTask.COMPLETED).all()
        return queryset