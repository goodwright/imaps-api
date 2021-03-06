# Generated by Django 2.2.16 on 2020-11-15 14:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'groups',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('username', models.SlugField(max_length=30, unique=True)),
                ('email', models.EmailField(max_length=200, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.IntegerField(default=None, null=True)),
                ('creation_time', models.IntegerField(default=0)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'users',
                'ordering': ['creation_time'],
            },
        ),
        migrations.CreateModel(
            name='GroupInvitation',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('creation_time', models.IntegerField(default=0)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_invitations', to='core.Group')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_invitations', to='core.User')),
            ],
            options={
                'db_table': 'group_invitations',
                'ordering': ['creation_time'],
            },
        ),
        migrations.AddField(
            model_name='group',
            name='admins',
            field=models.ManyToManyField(related_name='admin_groups', to='core.User'),
        ),
        migrations.AddField(
            model_name='group',
            name='users',
            field=models.ManyToManyField(related_name='groups', to='core.User'),
        ),
    ]
