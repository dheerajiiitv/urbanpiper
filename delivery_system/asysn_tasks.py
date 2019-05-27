
import json

from channels import Group
from channels.auth import channel_session_user
from django.core import serializers

from delivery_system.models import DeliveryTask, StateDeliveryTask

@channel_session_user
def ws_connect(message):
    Group('new-tasks').add(message.reply_channel)
    message.channel_session['task'] = 'new-tasks'
    message.reply_channel.send({
        'accept': True
    })


@channel_session_user
def ws_receive(message):
    data = json.loads(message.content.get('text'))
    if data.get('evt') == 'new_tasks':
        Group('new-tasks').add(message.reply_channel)
        message.channel_session['task'] = 'new-tasks'
        ordered = get_new_tasks()
        if ordered:
            Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", [ordered]),"type": 'TYPE_TASKS'})})
        else:
            Group('new-tasks').send({"text": json.dumps({'data':serializers.serialize("json", []),"type": 'TYPE_TASKS'})})
        Group('notification').discard(message.reply_channel)
    elif data.get('evt') == 'notification':
        Group('notification').add(message.reply_channel)
        Group('new-tasks').discard(message.reply_channel)

        message.channel_session['task'] = 'notification'


    # Task with high priority than so on




@channel_session_user
def ws_disconnect(message):
    # user_group = message.channel_session
    # Group(user_group).discard(message.reply_channel)
    print("Disconnect")



def get_new_tasks():
    return DeliveryTask.objects.filter(current_state=StateDeliveryTask.NEW).order_by('priority').first()