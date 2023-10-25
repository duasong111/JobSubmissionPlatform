import datetime
import os
import time
import traceback
import json
from urllib.parse import urljoin

from django.http import HttpResponse
from api.napi import Login
from login.models import Students, Teacher
from utils.token import TokenValidate


# 写log函数
def write_educational_log(content):
    """
    write_educational_log() ->

    写入教务系统工作日志
    """
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists('logssss/educational'):
        os.mkdir('logssss/educational')

    def write():
        file_name = 'logssss/educational/' + date + '.log'
        if not os.path.exists(file_name):
            with open(file_name, mode='w', encoding='utf-8') as n:
                n.write('【%s】的日志记录' % date)
        with open(file_name, mode='a', encoding='utf-8') as l:
            l.write('\n%s' % content)

    write()


# 写log函数
def write_life_log(content):
    """
    write_life_log() ->

    写入生活服务工作日志
    """
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists('logssss/life'):
        os.mkdir('logssss/life')

    def write():
        file_name = 'logssss/life/' + date + '.log'
        if not os.path.exists(file_name):
            with open(file_name, mode='w', encoding='utf-8') as n:
                n.write('【%s】的日志记录' % date)
        with open(file_name, mode='a', encoding='utf-8') as l:
            l.write('\n%s' % content)

    write()


def write_school_info_log(content):
    """
    write_school_info_log() ->

    写入校园信息工作日志
    """
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists('logssss/school-info'):
        os.mkdir('logssss/school-info')

    def write():
        file_name = 'logssss/school-info/' + date + '.log'
        if not os.path.exists(file_name):
            with open(file_name, mode='w', encoding='utf-8') as n:
                n.write('【%s】的日志记录' % date)
        with open(file_name, mode='a', encoding='utf-8') as l:
            l.write('\n%s' % content)

    write()


# 写error_log函数
def write_exception_log(content, data=""):
    """
    write_exception_log() ->

    写入错误日志
    """
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists('logssss_error'):
        os.mkdir('logssss_error')

    def write():
        file_name = 'logssss_error/' + date + '.log'
        if not os.path.exists(file_name):
            with open(file_name, mode='w', encoding='utf-8') as n:
                n.write('【%s】的抛出错误日志记录' % date)
        with open(file_name, mode='a', encoding='utf-8') as l:
            l.write('\n----报错内容----')
            l.write('\n%s' % content)
            l.write('\n----数据----')
            l.write('\n%s' % str(data))
            l.write('\n----------------------俺是分割线----------------------')

    write()


def cache_data(xh, filename):
    """ 读取缓存数据 """
    # 半角转换为全角（避免程序将文件名识别为路径）
    filename = eval(repr(filename).replace('/', '／'))
    doc_url = 'data/' + str(xh)[0:4] + '/' + str(xh) + '/'
    file_url = doc_url + str(filename) + '.json'
    if not os.path.exists(doc_url):
        os.makedirs(doc_url)
    else:
        if not os.path.exists(file_url):
            return
        else:
            with open(file_url, mode='r', encoding='utf-8') as o:
                result = json.loads(o.read())
                if result.get("err"):
                    return
                return result


def new_data(xh, addition_path, file_name, content):
    """ 写入缓存数据 """
    # 半角转换为全角（避免程序将文件名识别为路径）
    file_name = eval(repr(file_name).replace('/', '／'))
    doc_url = 'data/' + str(xh)[0:4] + '/' + str(xh) + '/' + addition_path + '/'
    file_url = doc_url + str(file_name) + '.json'
    if not os.path.exists(doc_url):
        os.makedirs(doc_url)
        with open(file_url, mode='w', encoding='utf-8') as n:
            n.write(content)
    else:
        with open(file_url, mode='w', encoding='utf-8') as n:
            n.write(content)
    # if not os.path.exists(fileurl):
    #     with open(fileurl, mode='w', encoding='utf-8') as n:
    #         n.write(content)


def new_news_cache(url, content):
    """ 写入新闻缓存数据 """
    file_url = "data/news" + url
    file_name = os.path.basename(url)
    path_url = file_url.replace(file_name, '')
    if not os.path.exists(path_url):
        os.makedirs(path_url)
        with open(file_url, mode='w', encoding='utf-8') as n:
            n.write(str(content))
    else:
        with open(file_url, mode='w', encoding='utf-8') as n:
            n.write(str(content))


def read_news_cache(url):
    """ 读取新闻缓存数据 """
    file_url = "data/news" + url
    file_name = os.path.basename(url)
    path_url = file_url.replace(file_name, '')
    if not os.path.exists(path_url):
        os.makedirs(path_url)
    else:
        if not os.path.exists(file_url):
            return "{}"
        else:
            with open(file_url, mode='r', encoding='utf-8') as o:
                return o.read()


class MyEncoder(json.JSONEncoder):
    """
    MyEncoder() -> json

    自定义编码器，按UTF-8编码
    """

    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        return json.JSONEncoder.default(self, obj)


def build_resp_result(status_code, status_msg, data, cookies=None):
    """
    build_resp_result() -> HttpResponse

    返回一个http报文
    """
    if cookies is None:
        return HttpResponse(json.dumps({
            'status': status_code,
            'statusMsg': status_msg,
            'data': data
        }, cls=MyEncoder, ensure_ascii=False), content_type="application/json,charset=utf-8")
    else:
        rep = HttpResponse(json.dumps({
            'status': status_code,
            'statusMsg': status_msg,
            'data': data
        }, cls=MyEncoder, ensure_ascii=False), content_type="application/json,charset=utf-8")
        for key, value in cookies.items():
            rep.set_cookie(key, value)
        return rep


def get_user_ip(request):
    """
    get_user_ip() -> request

    返回用户访问IP
    """
    if request.META.get('HTTP_X_FORWARDED_FOR') is not None:
        return request.META['HTTP_X_FORWARDED_FOR']
    else:
        return request.META['REMOTE_ADDR']


def get_decrypt_userinfo(token: str):
    """
    get_decrypt_userinfo() -> dict

    返回用户名和密码
    字典内包含两个值：uid：学号/教工号，upass密码
    """
    tv = TokenValidate(token)
    s1 = tv.validate_token()
    if s1["code"] == 200 or s1["code"] == 402:
        decrypt_data = tv.decrypt_userinfo()
        if decrypt_data["code"] == 200:
            return decrypt_data["data"]
    raise Exception("get_decrypt_userinfo()函数出错")


def update_jw_cookies(user_id: str, user_pass: str):
    """
    update_jw_cookies() -> dict

    刷新教务系统cookies
    返回值包含三个参数：code：状态码，msg：消息，data：数据主体
    """
    try:
        start_time = time.time()
        lgn = Login()
        pre_login = lgn.login(user_id, user_pass)
        if pre_login["code"] == 1000 or pre_login["code"] == 1101:
            cookies = lgn.cookies
            new_jsessionid = cookies["JSESSIONID"]
            new_insert_cookie = cookies["insert_cookie"]
            update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if len(user_id) == 11:
                Students.objects.filter(student_id=int(user_id)).update(jsessionid=new_jsessionid,
                                                                        insert_cookie=new_insert_cookie,
                                                                        update_time=update_time)
            else:
                Teacher.objects.filter(teacher_id=int(user_id)).update(jsessionid=new_jsessionid,
                                                                       insert_cookie=new_insert_cookie,
                                                                       update_time=update_time)
            end_time = time.time()
            spend_time = end_time - start_time
            content = ('【%s】[%s]更新cookies成功，耗时%.2fs' % (
                datetime.datetime.now().strftime('%H:%M:%S'), user_id, spend_time))
            print(content)
            write_educational_log(content)
            return {"code": 1000, "msg": pre_login['msg'], "data": pre_login['data']}
        else:
            # 登录失败
            content = ('【%s】[%s]在登录时出错，因为[%s]' % (
                datetime.datetime.now().strftime('%H:%M:%S'), user_id, pre_login['msg']))
            print(content)
            write_educational_log(content)
            return {"code": pre_login['code'], "msg": pre_login['msg'],
                    "data": {} if pre_login.get("data") is None else pre_login["data"]}
    except Exception as e:
        content = ('【%s】[%s]在调用<%s>函数时出错' % (
            datetime.datetime.now().strftime('%H:%M:%S'), user_id, "update_cookies"))
        print(content)
        write_educational_log(content)
        err_content = traceback.format_exc()
        print(err_content)
        write_exception_log(err_content, pre_login)
        return {"code": 999, "msg": "未知错误，详见日志", "data": err_content}


def cal_sex(id):
    try:
        sex_num = id[16:17]
        if int(sex_num) % 2 == 0:
            return 2
        else:
            return 1
    except Exception as e:
        return 1