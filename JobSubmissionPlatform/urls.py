
from django.contrib import admin
from django.urls import path, re_path,include
from django.views.static import serve
from django.conf import settings
from app1 import views
from app1.views import Inform, Students_view, Class, Community,upload,account,ShowMe

urlpatterns = [
    #这个是media的文件的固定要求
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}, name='media'),
    # path('login/')

    # 作业提交模块(学委查看页面)
    path('Inform/Homework/', Inform.Inform_list),
    path('Inform/add/', Inform.Inform_add),
    path('Inform/delete/', Inform.Inform_delete),
    path('Inform/detail/', Inform.Inform_detail),
    path('Inform/edit/', Inform.Inform_edit),
    path('Inform/multi/', Inform.Inform_multi),

    # 饼图的制作----先拿class页面进行设置
    path('Inform/pie/', Inform.Inform_pie),

    # 学生所能查看的页面以及设置--
    path('Students_view/Homework/', Students_view.View_add),
    path('Students_view/MyInform/', Students_view.View_My),
    path('Students_view/AddPortal/', Students_view.AddPortal),



    #这个是为了展现课表

    path('ShowMe/BasicInfor/',ShowMe.BasicInform),

    # 用户的登录管理
    path('login/', account.login),
    path('logout/',account.logout),

    # 照片
    path('image/code/', account.image_code),

    #班级列表
    path('Class/list/', Class.Class_list),
    path('Class/add/', Class.Class_add),

    #注意在使用删除，修改等操作时候，非ajax请求时，请注意要携带nid，否则报找不到路由

    # 社团活动
    path('Community/list/', Community.Community_list),
    path('Community/add/', Community.Community_add),
    path('Community/<int:nid>/delete/', Community.Community_delete),

    #这个对应的是引入model来进行数据提交的数据库
    path('upload/model/form/', upload.upload_modal_form),

]
