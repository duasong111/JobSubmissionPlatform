from django.shortcuts import render,HttpResponse,redirect
from django import forms
#引入教务系统的爬虫
from api.napi import Login, Info
from io import BytesIO
from app1.utils.bootstrap import BootStrapForm
from app1.utils.bootstrap import BootStrapModelForm
from app1.utils.encrypt import md5 #这个是没有用上的
from app1 import models
from app1.utils.code import check_code
class LoginForm(BootStrapForm):
    username=forms.CharField(
        label="用户名",
        widget=forms.TextInput,
        required=True
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput,
        required=True
    )
    code = forms.CharField(
        label="验证码",
        widget=forms.TextInput,
        required=True
    )
#这个是经过加密，先进行取消，到时候进行两种形式的，先加密再解密
    # def clean_password(self):
    #     pwd=md5(self.cleaned_data.get("password"))
    #     return pwd
#一会来进行设置两个登录的方式，教务系统和那个管理员
def login(request):
    """登录页面"""
    if request.method=="GET":
        form=LoginForm()
        return render(request,'login.html',{"form":form})
    form=LoginForm(data=request.POST)
    if form.is_valid():
        # print(form.cleaned_data) #来显示提交的信息
        username=form.cleaned_data['username']
        password=form.cleaned_data['password']
        # if username not in models.UserInfo.objects.filter(username=username).first():
        #     models.UserInfo.objects.update(username=username,password=password)

        LG=Login_test(username=username,password=password) #用作登录
        data=LG.login_test1()

        user_input_code=form.cleaned_data.pop('code')
        code=request.session.get('image_code','')
        if code.upper()!= user_input_code.upper():
            form.add_error("code",'验证码错误')
            return render(request, 'login.html',{"form": form})

        admin_object=models.StuInfo.objects.filter(**form.cleaned_data).first()
        # print(admin_object) #获取第一个值也就是其名称
        #这个是用教务系统进行登录
        if data['code'] != 1000:
            form.add_error("password", "用户名或密码错误")
            return render(request, 'login.html', {"form": form})


        #存储教务系统的cookie值
        request.session["info"]=data['data']['cookies'] #教务系统

        # global sharedata #先声明是全局变量，然后再进行赋值
        # sharedata = f"{request.session['info']}"
        # # print(sharedata)

        # request.session["info"]={"id":admin_object.id,"name":admin_object.username} #数据库

        request.session.set_expiry(60*60*24*7)
        #这个是相当于自己去设置Sessionid

        #在这先暂时去找一个返回的页面--登录成功的
        return redirect("/Inform/Homework/")
    return render(request, 'login.html', {"form": form})

"""这个是引入教务系统的登录"""
class Login_test(object):
    def __init__(self,username,password):
        self.username=username
        self.password=password
    def login_test1(self):
        LG=Login()
        result = LG.login(f'{self.username}', f'{self.password}')
        if result['code'] == 1000:
            user = models.UserInfo.objects.filter(name=self.username).first()
            if user:
                user.password = self.password
                user.save()
            else:
                new_user = models.UserInfo(name=self.username, password=self.password)
                new_user.save()

        return result

    # def get_shared_data(self):
    #     """将获取的cookie值来传递给其他的，避免再次登录"""
    #     global sharedata
    #     sharedata = self.shared_value
    #     return  sharedata


def image_code(request):
    """生成验证图片"""
    img,code_string=check_code()
    #写入到自己的session文件中
    request.session['image_code']=code_string
    #对于session来进行60S的超时校验
    request.session.set_expiry(60)

    # print(code_string)
    stream = BytesIO()
    img.save(stream, 'png')

    return HttpResponse(stream.getvalue())
def logout(request):
    """ 注销 """
    request.session.clear()
    return redirect('/login/')
