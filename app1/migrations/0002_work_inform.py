# Generated by Django 3.2.20 on 2023-07-05 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Work_inform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inform', models.CharField(max_length=32, verbose_name='通知')),
                ('create_time', models.DateField(verbose_name='通知时间')),
            ],
        ),
    ]
