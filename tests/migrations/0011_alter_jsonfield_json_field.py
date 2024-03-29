# Generated by Django 3.2.13 on 2022-06-01 13:05

from django.db import migrations, models
import concrete_datastore.concrete.models
from django.conf import settings
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('concrete', '0010_auto_20210915_0901'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jsonfield',
            name='json_field',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name='SecureConnectCode',
            fields=[
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('modification_date', models.DateTimeField(auto_now=True)),
                ('expired', models.BooleanField(default=False)),
                ('mail_sent', models.BooleanField(default=False)),
                ('uid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('value', models.CharField(default=concrete_datastore.concrete.models.get_random_secure_connect_code, max_length=250)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='secure_connect_codes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
