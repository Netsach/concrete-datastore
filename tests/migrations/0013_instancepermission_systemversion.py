# Generated by Django 3.2.16 on 2023-02-15 14:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('concrete', '0012_auto_20221115_0644'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemVersion',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('app_name', models.CharField(db_index=True, max_length=255)),
                ('is_latest', models.BooleanField(default=True)),
                ('modification_date', models.DateTimeField(auto_now=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='InstancePermission',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('model_name', models.CharField(db_index=True, default='', max_length=255)),
                ('read_instance_uids', models.JSONField(default=list)),
                ('write_instance_uids', models.JSONField(default=list)),
                ('modification_date', models.DateTimeField(auto_now=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='instance_permissions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
