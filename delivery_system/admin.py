from django.contrib import admin
from .models import DeliveryTask, StateDeliveryTask, Staff
# Register your models here.
admin.site.register(DeliveryTask)
admin.site.register(StateDeliveryTask)
admin.site.register(Staff)
