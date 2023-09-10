from django.shortcuts import render,redirect
from app1 import  models
from django.core.validators import ValidationError
from django.core.validators import RegexValidator
from django import forms
from app1.utils.bootstrap import BootStrapModelForm
from app1.utils.encrypt import md5   #导入自定义方法，进行哈希加密
def admin_list(request):
    """管理员"""
    quaryset = models.StuInfo.objects.all()
    contest={
         "quaryset":quaryset
    }
    return render(request,'Class_Information.html',contest)
class AdminModelForm(BootStrapModelForm):
    confirm_password=forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(render_value=True)
    )
    password = forms.CharField(
        label='输入密码',
        widget=forms.PasswordInput(render_value=True)
    )
   # 这个就是对那个password也进行密码隐藏
    class Meta:
        model=models.StuInfo
        fields={"username",'password','confirm_password'}

    def clean_password(self):
        pwd=md5(self.cleaned_data.get("password")) #直接经过md5然后进行返回数据
        return pwd  #经过md5的哈希进行加密
    def clean_confirm_password(self):
        # print("pwd的值是:{}".format(self.cleaned_data.get("password")))  # 输出测试
        pwd=self.cleaned_data.get("password")

        # print(self.cleaned_data)
        confirm=md5(self.cleaned_data.get("confirm_password")) #确认密码也加密
        # print("confirm的值是:{}".format(confirm))
        # print("pwd的值是:{}".format(self.cleaned_data.get("password")))  # 输出测试
        if confirm != pwd:
            raise ValidationError("密码不一样")
        return confirm
# def admin_add(request):
#     """添加管理员"""
#     title = "新建管理员"
#     if request.method =="GET":
#         form = AdminModelForm()
#         return render(request,'change.html',{'form':form,'title':title})
#     form=AdminModelForm(data=request.POST)
#     if form.is_valid():
#         form.save()
#         return redirect('/admin/list')
#     return render(request,'change.html',{'form':form,'title':title})



class AdminEditModelForm(BootStrapModelForm):
    class Meta:
        model = models.StuInfo
        fields = {'username'}
#只进行用户名的编辑



#下边是管理员来进行密码的重置
# class AdminresetModelForm(BootStrapModelForm):
#     confirm_password = forms.CharField(
#         label="确认密码",
#         widget=forms.PasswordInput(render_value=True)
#     )
#     password = forms.CharField(
#         label='输入密码',
#         widget=forms.PasswordInput(render_value=True)
#     )
#     class Meta:
#         model = models.StuInfo
#         fields = {'password','confirm_password'}
#
#     def clean_password(self):
#         pwd = self.cleaned_data.get("password")
#         md5_pwd = md5(pwd) #去检验是否和上个密码一样
#         exists=models.StuInfo.objects.filter(id=self.instance.pk,password=md5_pwd).exists()
#         if exists:
#             raise ValidationError("不能和原密码相同")
#         return md5(pwd)
#
#     def clean_confirm_password(self):
#         pwd = self.cleaned_data.get("password")
#         # print("pwd的值是:{}".format(self.cleaned_data.get("password"))) #输出测试
#         # print(self.cleaned_data)
#         confirm = md5(self.cleaned_data.get("confirm_password"))  # 确认密码也加密
#         # print("输出:{}".format(confirm))
#         if confirm != pwd:
#             raise ValidationError("密码不一样")
#         return confirm

# def admin_edit(request,nid):
#     row_object=models.StuInfo.objects.filter(id=nid).first()
#     if not row_object:
#         return redirect('/admin/list')
#     title = "编辑管理员"
#     if request.method=="GET":
#         form = AdminEditModelForm(instance=row_object)
#         return  render(request,'admin_edit.html',{"form":form,'title':title})
#     form=AdminEditModelForm(data=request.POST,instance=row_object)
#     if form.is_valid():
#         form.save()
#         return redirect('/admin/list/')
#     return render(request,'change.html',{"form":form,'title':title})
#
# def admin_delete(request, nid):
#     """管理员账号的删除"""
#     models.StuInfo.objects.filter(id=nid).delete()
#     return redirect('/admin/list/')
# def admin_reset(request, nid):
#     """密码的重置"""
#     row_object = models.Admin.objects.filter(id=nid).first()
#     if not row_object:
#         return redirect('/admin/list')
#     title="重置密码:--{}".format(row_object.username)
#     if request.method=="GET":
#         form=AdminresetModelForm()
#         return render(request, 'change.html', {'title': title,'form':form})
#
#     form=AdminresetModelForm(data=request.POST,instance=row_object)
#     if form.is_valid():
#         form.save()
#         return redirect('/admin/list/')
#     return render(request, 'change.html', {'title': title, 'form': form})

