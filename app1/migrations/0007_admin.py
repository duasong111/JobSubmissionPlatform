# Generated by Django 3.2.20 on 2023-07-14 00:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0006_rename_name_stuinfo_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='Admin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=32, verbose_name='用户名')),
                ('password', models.CharField(max_length=64, verbose_name='密码')),
            ],
        ),
    ]
