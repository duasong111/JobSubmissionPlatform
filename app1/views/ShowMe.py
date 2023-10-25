from urllib import request

from django.shortcuts import render,HttpResponse,redirect
from api.napi import Info
from app1.views.account import LoginForm
from api.news_api import SchoolNews
from api.MessagePort import MessageLoginPortal

def BasicInform(request):
    info = request.session["info"]
    IF = Info(cookies=info)
    MyInform = IF.getPersonInfo()
    MyDatas = MyInform['data']
    me=IF.getCollegesList()
    CollageLists=IF. getTeachingPlanCollegesList()
    classPlans= IF.getMajorList(college_id="2021")
    form = LoginForm()
    #校园新闻
    News=SchoolNews()
    news=News.getNewsListByCat('10307',1)
    newsList = news['data']
    context = {
        'title':"校园新闻",
        # "queryset":news,
        'Me': me,
        "queryset":newsList,
        'info111':MyDatas,
        'CollageLists':CollageLists,
        'classPlans':classPlans,
        'form':form
    }
    return render(request,'ShowMe.html',context)

