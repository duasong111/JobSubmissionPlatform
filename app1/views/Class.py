from django.shortcuts import HttpResponse,redirect,render
from django.views.decorators.csrf import csrf_exempt
from app1.utils.bootstrap import BootStrapModelForm
from django.http import JsonResponse
from app1 import models
from openpyxl import load_workbook
from datetime import datetime
class InformModelForm(BootStrapModelForm):
    class Meta:
        model = models.Class_list
        fields = "__all__"
def Class_list(request):
    # 到时候可以按照学号列表来进行排列
    queryset = models.Class_list.objects.all()
    form = InformModelForm()
    context = {
        "form": form,
        "queryset": queryset
    }
    return render(request, 'Class_Information.html', context)
@csrf_exempt
def Class_add(request):
    """添加同学"""
    form = InformModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({"status": True})
    return JsonResponse({"status": True, "error": form.errors})