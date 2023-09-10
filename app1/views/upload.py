from django.forms import models
from django.forms import ModelForm
from django.shortcuts import render,HttpResponse,redirect
from django import forms
from app1 import  models
from django.conf import settings
from app1.utils.bootstrap import BootStrapForm
from app1.utils.bootstrap import BootStrapModelForm
import os
# def upload_list(request):
#   """文件上传设置"""
#   if request.method=="GET":
#       return render(request,'uploadlist.html')
#   """
#   #使用POST请求的时候会将
#   <QueryDict:
#    {'csrfmiddlewaretoken': ['8hzoMefPGbDlRjxHlMYKzQeOBAXoE5zIaBbC7sufiI6N87yQdzKL3M8vSMpTfFat'],
#   'username': ['duasong'], 'avatar': ['20211101059余鑫荣.docx']}>
#   """
#   # print(request.POST)
#   # print(request.FILES)
#   """如果在form中添加了 <form method="post" enctype="multipart/form-data">
#   则会显示数据 <MultiValueDict: {'avatar': [<InMemoryUploadedFile: 20211101059余鑫荣.docx (application/vnd.openxmlformats-officedocument.wordprocessingml.document)>]}>
#   """
#
#   file_object=request.FILES.get("avatar")
#   # print(file_object.name)   #以上两行来获取文件的名称
#   # f=open(file_object,mode='wb')
#   # for chunk in file_object.chunks():
#   #     f.write(chunk)
#   # f.close()
#
#
#   return HttpResponse("返回数据成功")
#
# #上传文件到数据库
#
#
#
# class UpForm(BootStrapForm):
#     bootstrap_exclude_fields = ['img']
#     name = forms.CharField(label="姓名")
#     age = forms.IntegerField(label="年龄")
#     img = forms.FileField(label="头像")
#
#
# def upload_form(request):
#     title = "Form上传"
#     if request.method == "GET":
#         form = UpForm()
#         return render(request, 'upload_form.html', {"form": form, "title": title})
#
#     form = UpForm(data=request.POST, files=request.FILES)
#     if form.is_valid():
#
#         image_object = form.cleaned_data.get("img")
#
#
#
#
#
#         # file_path = "app01/static/img/{}".format(image_object.name)
#         # media_path = os.path.join(settings.MEDIA_ROOT, image_object.name)
#         media_path = os.path.join("media", image_object.name)
#
#         f = open(media_path, mode='wb')
#         for chunk in image_object.chunks():
#             f.write(chunk)
#         f.close()
#
#         # 2.将图片文件路径写入到数据库
#         # models.
#         models.Boss.objects.create(
#             name=form.cleaned_data['name'],
#             age=form.cleaned_data['age'],
#             img=media_path,
#         )
#         return HttpResponse("...")
#     return render(request, 'upload_form.html', {"form": form, "title": title})

class UpModelForm(BootStrapModelForm):
    bootstrap_exclude_fields = ['img']
    class Meta:
        model =models.CommunityActive
        fields="__all__"
def upload_modal_form(request):
    """ 上传文件和数据（modelForm）"""
    title = "ModelForm上传文件"
    if request.method == "GET":
        form = UpModelForm()
        return render(request, 'upload_form.html', {"form": form, 'title': title})

    form = UpModelForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        form.save()
        return redirect("/Community/list/")
    return render(request, 'upload_form.html', {"form": form, 'title': title})



