from django.db import models

# Create your models here.
class Class_list(models.Model):
    """班级表---范围更大一些"""
    name=models.CharField(verbose_name="姓名",max_length=32)
    schoolID= models.CharField(verbose_name="学号", max_length=64)
    className=models.CharField(verbose_name="所在班级",max_length=32)
    bedroom = models.CharField(verbose_name="寝室", max_length=32)
    QQID = models.CharField(verbose_name="QQ", max_length=64)
    phoneID = models.CharField(verbose_name="微信", max_length=64)

    def __str__(self):
        return self.className

"""问题！！！！！数据库的时间需要去进行更改"""

class UserInfo(models.Model):
    """用户使用学号来进行登录--范围小一些"""
    name = models.CharField(verbose_name="姓名", max_length=16)
    password = models.CharField(verbose_name="密码", max_length=64)
"""目前这个仅仅是为了我进行测试去写的测试"""
class stuLogin(models.Model):
    name = models.CharField(verbose_name="用户名",max_length=16)
    password = models.CharField(verbose_name="密码",max_length=64)
class teacher(models.Model):
    name = models.CharField(verbose_name="用户名",max_length=16)
    password = models.CharField(verbose_name="密码",max_length=64)



class Work_inform(models.Model):
    """作业通知表"""
    inform=models.CharField(verbose_name="通知",max_length=32)
    create_time = models.DateField(verbose_name="通知时间")
    level_choices = (
        (1, "正常作业"),
        (2, "一般提醒"),
        (3, "紧急通知"),
        (4, "紧急注意")
    )
    level = models.SmallIntegerField(verbose_name="级别", choices=level_choices, default=1)


class StuInfo(models.Model):
    """学生信息表"""
    username = models.CharField(verbose_name="网名", max_length=16)
    Stu_num = models.CharField(verbose_name="学号", max_length=64)
    password=models.CharField(verbose_name='密码',max_length=32)

    gender_choices = (
        (1, "男"),
        (2, "女"),
    )
    gender = models.SmallIntegerField(verbose_name="性别", choices=gender_choices)
    def __str__(self):
        return self.username

# img = models.FileField(verbose_name="Logo", max_length=128, upload_to='Community/')
class CommunityActive(models.Model):

    """社团活动"""
    title=models.CharField(verbose_name="主题",max_length=64)
    content=models.CharField(verbose_name="内容",max_length=128)
    place=models.CharField(verbose_name="地点",max_length=64)
    hold_time = models.DateField(verbose_name="举办时间")
    img = models.FileField(verbose_name="Logo", max_length=128, upload_to='Community/')
    active_types=(
        (1,"社团招新"),
        (2, "举办活动"),
        (3, "志愿参与"),
    )
    active=models.SmallIntegerField(verbose_name="活动类型",choices=active_types)

class Boss(models.Model):
    """老板"""
    name=models.CharField(verbose_name="姓名",max_length=32)
    age = models.IntegerField(verbose_name="年龄")
    img = models.CharField(verbose_name="头像", max_length=128)
class City(models.Model):
    """ 城市 """
    name = models.CharField(verbose_name="名称", max_length=32)
    count = models.IntegerField(verbose_name="人口")
    # 本质上数据库也是CharField，自动保存数据。
    img = models.FileField(verbose_name="Logo", max_length=128, upload_to='city/')