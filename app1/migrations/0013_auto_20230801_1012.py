# Generated by Django 3.2.20 on 2023-08-01 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0012_communityactive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communityactive',
            name='content',
            field=models.SmallIntegerField(verbose_name='内容'),
        ),
        migrations.AlterField(
            model_name='communityactive',
            name='place',
            field=models.SmallIntegerField(verbose_name='地点'),
        ),
        migrations.AlterField(
            model_name='communityactive',
            name='title',
            field=models.SmallIntegerField(verbose_name='主题'),
        ),
    ]
