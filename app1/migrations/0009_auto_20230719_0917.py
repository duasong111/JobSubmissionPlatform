# Generated by Django 3.2.20 on 2023-07-19 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0008_delete_admin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='class_list',
            name='title',
        ),
        migrations.AddField(
            model_name='class_list',
            name='QQID',
            field=models.CharField(default='1234', max_length=64, verbose_name='QQ'),
        ),
        migrations.AddField(
            model_name='class_list',
            name='className',
            field=models.CharField(default='计科2102', max_length=32, verbose_name='所在班级'),
        ),
        migrations.AddField(
            model_name='class_list',
            name='name',
            field=models.CharField(default='张三', max_length=32, verbose_name='姓名'),
        ),
        migrations.AddField(
            model_name='class_list',
            name='phoneID',
            field=models.CharField(default='1234', max_length=64, verbose_name='微信'),
        ),
        migrations.AddField(
            model_name='class_list',
            name='schoolID',
            field=models.CharField(default='2021111', max_length=64, verbose_name='学号'),
        ),
    ]