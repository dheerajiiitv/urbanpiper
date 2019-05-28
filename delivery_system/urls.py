from django.urls import path
from . import views
app_name = 'delivery_system'
urlpatterns = [
    path('home/', views.Home.as_view(), name='home'),
    path('home/create_task', views.AddDeliveryTaskView.as_view(), name='create_task'),
    path('home/tasks_list',  views.ListOfTasks.as_view(), name='tasks_list'),
    path('home/task_details/<int:pk>', views.DetailsOfTasks.as_view(), name='task_details'),
    path('home/delivery/accepted_task', views.DeliveryBoyAcceptedTasks.as_view(), name='accepted_tasks'),
    path('home/delivery/completed_task', views.CompletedTaskView.as_view(), name='completed_tasks'),
    path('home/delivery/decline_task/<int:page_number>/<int:id>', views.decline_task, name='decline_task'),
    path('home/delivery/complete_task/<int:page_number>/<int:id>', views.complete_task, name='complete_task'),
    path('home/delivery/accept_task/<int:id>', views.accept_task, name='accept_task'),
    path('home/manager/cancel_task/<int:page_number>/<int:id>', views.cancel_task, name='cancel_task'),
    path('home/delivery/accept_a_task', views.AcceptATask.as_view(), name='accept_a_task'),

]