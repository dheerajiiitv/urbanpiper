from django import template

register = template.Library()


@register.filter(name='get_priority')
def get_priority(p):
    a = {'0': 'HIGH', '1': 'MEDIUM', '2': 'LOW'}
    return a[str(p)]


@register.filter(name='get_state')
def get_state(p):
    a = {'0': 'New',
         '1': 'Accepted',
         '2': 'Completed',
         '3': 'Declined',
         '4': 'Cancelled'}
    return a[str(p)]
