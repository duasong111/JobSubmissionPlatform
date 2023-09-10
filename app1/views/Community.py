from django.shortcuts import HttpResponse,redirect,render
from django.views.decorators.csrf import csrf_exempt
from app1.utils.bootstrap import BootStrapModelForm
from django.http import JsonResponse
from app1 import models
class UpModelForm(BootStrapModelForm):
    bootstrap_exclude_fields = ['img']
    class Meta:
        model =models.CommunityActive
        fields="__all__"
def Community_list(request):
    # 到时候可以按照学号列表来进行排列
    queryset = models.CommunityActive.objects.all()
    form = UpModelForm()
    context = {
        "form": form,
        "queryset": queryset
    }
    return render(request, 'Community.html', context)
def Community_add(request):
    """使用modelForm来进行图片的保存，上传"""
    title = "ModelForm上传文件"
    if request.method == "GET":
        form = UpModelForm()
        return render(request, 'Community.html', {"form": form, 'title': title})

    form = UpModelForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        form.save()
        return HttpResponse("上传成功")
    return render(request, 'Community.html', {"form": form, 'title': title})
def Community_delete(request,nid):
    """进行数据的删除"""
    models.CommunityActive.objects.filter(id=nid).delete()
    return redirect("/Community/list/")