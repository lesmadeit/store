# Generated by Django 5.0.7 on 2024-11-27 12:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='state',
        ),
    ]