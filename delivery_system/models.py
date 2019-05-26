from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Staff(models.Model):
    USER_TYPE = (
        (0, 'Store Manager'),
        (1, 'Delivery Boy'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_list', verbose_name='Staff')
    user_type = models.IntegerField(choices=USER_TYPE)
    added_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def is_store_manager(self):
        if self.user_type == 0:
            return True
        return False

    def is_delivery_boy(self):
        if self.user_type == 1:
            return True
        return False


class DeliveryTask(models.Model):
    HIGH = 0
    MEDIUM = 1
    LOW = 2

    PRIORITIES = (
        (0, 'High'),
        (1, 'Medium'),
        (2, 'Low'),
    )
    title_name = models.CharField(max_length=255, verbose_name="Task Name")
    priority = models.IntegerField(choices=PRIORITIES,default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_manager_task')
    current_state=models.IntegerField(verbose_name='Current State', default=0)

    def __str__(self):
        return self.title_name
    class Meta:
        unique_together = ('title_name', 'created_by')

class StateDeliveryTask(models.Model):

    NEW = 0
    ACCEPTED = 1
    COMPLETED = 2
    DECLINED = 3
    CANCELLED = 4



    STATES = (
        (0, 'New'),
        (1, 'Accepted'),
        (2, 'Completed'),
        (3, 'Declined'),
        (4, 'Cancelled'),

    )
    delivery_tak = models.ForeignKey(DeliveryTask, on_delete=models.CASCADE, related_name='task_state')
    state = models.IntegerField(choices=STATES, default=0)
    state_change_date = models.DateTimeField(auto_now=True)
    state_change_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='state_change_user')

    def __str__(self):
        return self.delivery_tak.title_name + ' ' + str(self.state)

    class Meta:
        ordering = ['state_change_date']