from django.shortcuts import render,HttpResponse,redirect
from django.http import JsonResponse
from django import forms
from app1.utils.bootstrap import BootStrapModelForm, BootStrapForm
from app1 import  models
from app1.views.account import  Login_test
from api.napi import Login, Info
from api.news_api import SchoolNews
from api.MessagePort import MessageLoginPortal
# Create your views here.
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
#实现教务系统的登录
class LoginPortal(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
    def login_potral(self):
        LGP = MessageLoginPortal()
        result = LGP.login(f'{self.username}', f'{self.password}')
        return result


class InformModelForm(BootStrapModelForm):
    class Meta:
        model = models.Work_inform
        fields = "__all__"
        exclude = ["create_time"]  # 将这个内容不显示
def View_add(request):
    form = InformModelForm(data=request.POST)
    if form.is_valid():
    #     # print(form.cleaned_data) #来显示提交的信息
        username=form.cleaned_data['username']
        password=form.cleaned_data['password']
        LG=LoginPortal(username=username,password=password) #用作登录
        back=LG.login_potral()

        if back['code'] != 1000:
            form.add_error("password", "用户名或密码错误")
            # return render(request, 'login.html', {"form": form})
        request.session["info111"] = back['data']['cookies']  # 教务系统
    context = {
        'title': "这个是新的页面哎",
    }
    return render(request, 'ShowMe.html',context)
def View_My(request):
    info = request.session["info"] #保存的cookie值，这样就可以去进行其他页面的数据加载了
    IF=Info(cookies=info)
    MyInform=IF.getPersonInfo()
    MyDatas=MyInform['data']
    Me=MyInform['data']['name']
    # SchoolID=MyInform['data']['studentId']
#后续进行添加，做成可交互式的，就是可以选择的那种类型
    News=SchoolNews()
    news=News.getNewsListByCat('10307',1)
    news=news['data']
    form = LoginForm()
    context = {
        "MyInform":  MyInform,
        'title':"校园新闻",
        "queryset":news,
        'MeInform':Me,
        'MyDatas':MyDatas,
        "form": form
    }
    return render(request,'Students_view.html',context)
def AddPortal(request):
    pass

