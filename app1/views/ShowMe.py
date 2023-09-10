from django.shortcuts import render,HttpResponse,redirect
from api.napi import Info
from app1.views.account import LoginForm
from api.news_api import SchoolNews
from api.MessagePort import MessageLoginPortal
class LoginPortal(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
    def login_potral(self):
        LGP = MessageLoginPortal()
        result = LGP.login(f'{self.username}', f'{self.password}')
        return result

def BasicInform(request):
    # info = request.session["info"] #保存的cookie值，这样就可以去进行其他页面的数据加载了
    # IF=Info(cookies=info)
    # data=IF.getPersonInfo()

    # 这个是获取信息门户的 sessionID
    # 这个是获取信息门户的 sessionID
    # global context
    form=LoginForm(data=request.POST)
    if form.is_valid():
        Username = form.cleaned_data['username']
        Password = form.cleaned_data['password']
        LG = LoginPortal(username=Username, password=Password)  # 用作登录
        back = LG.login_potral()
        # print(f"22----{back}")
        # #其实这个时候已经获得了那个信息门户的一些cookie

        if back['code'] != 1000:
            form.add_error("password", "用户名或密码错误")
            # 存储教务系统的cookie值
        request.session["LoginPortal"] = back['data']['cookies']  # 教务系统
        # print(back)



        # request.session["info"] = data['data']['cookies']  # 教务系统
    # return HttpResponse("11111111")
    return render(request,'ShowMe.html')
