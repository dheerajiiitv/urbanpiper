# Generated by Django 2.2.1 on 2019-05-23 18:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('delivery_system', '0004_auto_20190523_2330'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deliverytask',
            name='title_slag',
        ),
    ]
