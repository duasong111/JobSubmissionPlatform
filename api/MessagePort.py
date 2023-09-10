# 信息门户登录
# 获取信息门户的Ajax数据
from pprint import pprint

import requests
import re
from lxml import etree
from urllib.parse import urljoin
from pyquery import PyQuery as pq
from requests import exceptions

BASE_URL = 'https://portal.wsyu.edu.cn'
BASE_URL_NET = 'https://portal.wsyu.edu.cn:8443'
BASE_URL_Appace = "https://portal.wsyu.edu.cn:8443/portal.do"
TIMEOUT = 5
class MessageLoginPortal(object):
    """登录类"""
    def __init__(self, cookies={}):
        self.login_url_nodomain = "/zfca/login"
        self.login_url = urljoin(BASE_URL, "/zfca/login")
        self.GetInform = urljoin(BASE_URL_NET, "/dwr/call/pl aincall/webServiceAjax.getWebserviceContags.dwr")
        self.headers = requests.utils.default_headers()
        self.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        self.headers["Sec-Fetch-Dest"] = "document"
        self.headers["Sec-Fetch-Mode"] = "navigate"
        self.headers["Sec-Fetch-Site"] = "none"
        self.headers["Sec-Fetch-User"] = "?1"
        self.headers["Sec-Ch-Ua"] = '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"'
        self.headers["Sec-Ch-Ua-Mobile"] = "?0"
        self.headers["Sec-Ch-Ua-Platform"] = "windows"
        self.headers["Host"] = "portal.wsyu.edu.cn"
        self.headers["Referer"] = self.login_url
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = cookies

    def login(self, username, password):
        """进行登录"""
        # 请求登录首页
        req_lt = self.sess.get(
            self.login_url,
            headers=self.headers,
            timeout=TIMEOUT
        )
        # 记录Set-Cookie的值，此时应只有JSESSIONID
        self.cookies = req_lt.cookies
        # 解析lt的值
        doc = pq(req_lt.text)
        input_element = doc('input[name="lt"]')
        lt_value = input_element.attr('value')
        # 构造请求数据表单
        login_data = {
            "useValidateCode": 0,
            "isremenberme": 1,
            "ip": '',
            "losetime": 30,
            "username": username,
            "password": password,
            "lt": lt_value,
            "_eventId": "submit",
            "submit1": "%B5%C7%C2%BC"
        }
        # print(self.cookies)
        # 携带密码发送请求
        req_login1 = self.sess.post(
            f'{self.login_url};jsessionid={self.cookies["JSESSIONID"]}',
            headers=self.headers,
            cookies=self.cookies,
            data=login_data,
            timeout=TIMEOUT,
            allow_redirects=False   # IMPORTANT 在这一步关闭重定向，以免自动跳转了
        )
        # print(req_login1.text)
        # 如果不是302状态码，证明密码错误或者其他原因
        if req_login1.status_code != 302:
            # NOTE 此处，由于在信息门户网页中，密码登录等报错信息是由js和css代码控制，所以只能直接判断bytes的用户名或密码错误这几个字符是否包含在主体中。
            # （因为如果首次访问时，html代码中并不包含这几个字，详见https://portal.wsyu.edu.cn/zfca/login的第214行左右）
            # 另外，由于信息门户网页编码为gbk，且部分字符不是标准的gbk编码，直接转换req_login.content会出错，所以只能像上面那么写。
            if bytes("用户名或密码错误", encoding='gbk') in req_login1.content:
                return {"code": 1002, "msg": "用户名或密码不正确"}
        # 此处可以忽略req_login1所携带的Set-Cookie，CASPRIVACY过期时间为1970.00.00.00，所以可忽略，CASTGC作用域path为/zfca，下一个重定向路径并不是这个，所以也可忽略
        req_login2 = self.sess.post(
            req_login1.headers["Location"],
            headers=self.headers,
            cookies=self.cookies,
            timeout=TIMEOUT,
            allow_redirects=False
        )
        # 此处需要记住这个请求所设置的cookie的值
        self.cookies = req_login2.cookies
        req_login3 = self.sess.get(
            req_login2.headers["Location"],
            headers=self.headers,
            cookies=self.cookies,
            timeout=TIMEOUT,
            allow_redirects=False
        )
        # print(f"login4{req_login3.text}")
        req_login4 = self.sess.get(
            req_login3.headers["Location"],
            headers=self.headers,
            cookies=self.cookies,
            timeout=TIMEOUT,
            allow_redirects=False
        )
        # print(req_login4.url)
        # 以上就是登录的所有请求流程，后期也可以改为req_login=xxxx，可以覆盖之前的变量，也可以不改，方便理解（反正也占不了多少内存）
        if req_login4.status_code == 200:
            return {
                "code": 1000,
                "msg": "信息门户信息",
                "data": {
                    "JSESSIONID": self.cookies["JSESSIONID"],
                    "URL":req_login4.url
                }
            }
        else:
            return { "code": 999, "msg": "未知原因登录失败"}
class Info(object):
    """获取信息"""
    def __init__(self,cookies,url,User,Pwd):
        """这里多获取了URL USER PWD 分别用作负载的page和请求头的Cookie"""
        self.GetSessionId = urljoin(BASE_URL_NET, "/dwr/engine.js")  # 获取scriptsessionId
        self.GetInform = urljoin(BASE_URL_NET, "/dwr/call/plaincall/webServiceAjax.getWebserviceContags.dwr")  # 饭卡余额
        self.main_url=url,
        """标准化写法(但是我会运行错误，显示应该是string不是tuple)--存在错误，采用第二种方法去写headers"""
        # self.headers = requests.utils.default_headers()
        # self.headers["Host"] = "portal.wsyu.edu.cn:8443",
        # self.headers["Content-Type"] = "text/plain",
        # self.headers["Accept"]="*/*",
        # self.headers["Referer"] = f"{self.main_url[0]}",
        # self.headers["Cookie"] = f"rememberUser=20211101052; rememberPassword=zzx021121..; JSESSIONID={cookies}",
        # self.headers[
        #     "User-Agent"
        # ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"

        #第二种写headers，为了将这些简化，采用不正规的手段
        self.headers={
            "Host": "portal.wsyu.edu.cn:8443",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Content-Type": "text/plain",
            "Accept": "*/*",
            "Referer": f"{self.main_url[0]}",
            "Cookie": f"rememberUser={User}; rememberPassword={Pwd}; JSESSIONID={cookies}"
        }
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = cookies
        # etree.
    def getscriptSessionId(self):
        """获取scriptSessionID"""
        response = requests.get(self.GetSessionId)
        if response.status_code == 200:
            content = response.text
            pattern = r'dwr.engine._origScriptSessionId = "(.*?)"'
            match = re.search(pattern, content)
            if match:
                return match.group(1)
            else:
                return "完蛋，请求不了，后续都不行"
        else:
            print(f"Failed to retrieve content. Status code: {response.status_code}")
    def GetTheBalance(self):
        url = "https://portal.wsyu.edu.cn:8443/dwr/call/plaincall/webServiceAjax.getService.dwr" #获取饭卡余额
        """获取饭卡余额"""
        script_session_id=Info.getscriptSessionId(self)
        payload = {
            "callCount": "1",
            "page": f"/{self.main_url[0][32:]}",
            "httpSessionId": f"{self.cookies}",
            "scriptSessionId": f"{script_session_id}",
            "c0-scriptName": "webServiceAjax",
            "c0-methodName": "getService",
            "c0-id": "0",
            "c0-param0": "string:displayDataID152222748749059847isCompTab",
            "c0-param1": "string:152222748749059847",
            "c0-param2": "string:空α空",
            "batchId": "14"
        }
        response = requests.post(url, data=payload, headers=self.headers)
        match = re.search(r'"(\d+\.\d+)"', response.text)
        if match:
            result = match.group(1)
            return {
                "code": 1000,
                "msg": "",
                "data": {
                    "balance": result,
                }
            }
        else:
            return { "code": 999, "msg": "未知原因获取失败"}
    def GetMyApply(self):
        url='https://portal.wsyu.edu.cn:8443/dwr/call/plaincall/portalAjax.getAppList.dwr'
        try:
            script_session_id = Info.getscriptSessionId(self)
            payload = {
                "callCount": "1",
                "page": f"/{self.main_url[0][32:]}",
                "httpSessionId": f"{self.cookies}",
                "scriptSessionId": f"{script_session_id}",
                "c0-scriptName": "portalAjax",
                "c0-methodName": "getAppList",
                "c0-id": "0",
                "c0-param0": "string:134871271995438017",
                "batchId": "5"
            }
            response = requests.post(url, data=payload, headers=self.headers)
            pattern = r'<h5>([^<]+)</h5>'   #只是匹配的应用的名称，没有匹配其网址
            result=[]
            matches = re.findall(pattern, response.text)
            for i in range(len(matches)):
                T=matches[i].encode('utf8').decode('unicode_escape')
                result.append(T)
            return {"code": 1000, "msg": "获取信息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取信息失败"}
    def GetMyBooks(self):
        url='https://portal.wsyu.edu.cn:8443/dwr/call/plaincall/webServiceAjax.getService.dwr'
        try:
            script_session_id = Info.getscriptSessionId(self)
            payload = {
                "callCount": "1",
                "page": f"/{self.main_url[0][32:]}",
                "httpSessionId": f"{self.cookies}",
                "scriptSessionId": f"{script_session_id}",
                "c0-scriptName": "webServiceAjax",
                "c0-methodName": "getService",
                "c0-id": "0",
                "c0-param0": "string:displayDataID152359307026486627isCompTab",
                "c0-param1": "string:152359307026486627",
                "c0-param2": "string:空α空",
                "batchId": "4"
            }
            response = requests.post(url, data=payload, headers=self.headers)
            pattern = r's\d+.[\w]{5,11}="([^"]*)"' # 只是匹配的 书籍名称 借书时间 归还时间 三个值
            result = []
            matches = re.findall(pattern, response.text)
            books=int(len(matches) / 3)
            for i in range(len(matches)):
                T = matches[i].encode('utf8').decode('unicode_escape')
                result.append(T)
            if len(result) < 1:
                return {"code": 200,"借阅书籍本数:":books ,"msg": "获取信息成功", "data": "您好像没有借书哦！"}
            else:
                return {"code": 200,"借阅书籍本数:":books , "msg": "获取信息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取超时"}
    def GetOfficeHall(self):
        url='https://portal.wsyu.edu.cn:8443/dwr/call/plaincall/portalAjax.getAppList.dwr'
        try:
            script_session_id = Info.getscriptSessionId(self)
            payload = {
                "callCount": "1",
                "page": f"/{self.main_url[0][32:]}",
                "httpSessionId": f"{self.cookies}",
                "scriptSessionId": f"{script_session_id}",
                "c0-scriptName": "portalAjax",
                "c0-methodName": "getAppList",
                "c0-id": "0",
                "c0-param0": "string:150174137013935481",
                "batchId": "8"
            }
            response = requests.post(url, data=payload, headers=self.headers)
            pattern = r'<h5>([^<]+)</h5>'
            result=[] #将这些东西都存进去
            matches = re.findall(pattern,response.text)
            for i in range(len(matches)):
                T = matches[i].encode('utf8').decode('unicode_escape')
                result.append(T)
            return {"code": 200, "msg": "获取信息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取信息失败"}

    def GetNewsList(self):
        url='https://portal.wsyu.edu.cn:8443/dwr/call/plaincall/webServiceAjax.getWebserviceContags.dwr'
        try:
            script_session_id = Info.getscriptSessionId(self)
            payload = {
                "callCount": "1",
                "page": f"/{self.main_url[0][32:]}",
                "httpSessionId": f"{self.cookies}",
                "scriptSessionId": f"{script_session_id}",
                "c0-scriptName": "webServiceAjax",
                "c0-methodName": "getWebserviceContags",
                "c0-id": "0",
                "c0-param0": "string:140236654520046316",
                "c0-param1":"string:1",
                "batchId": "1"
            }
            response = requests.post(url, data=payload, headers=self.headers)
            pattern = r"title=\\'([^<]+)"  #粗略的转化一下，没有匹配网址
            result = []  # 将这些东西都存进去
            matches = re.findall(pattern, response.text)
            for i in range(len(matches)):
                T = matches[i].encode('utf8').decode('unicode_escape')
                result.append(T)
            return {"code": 200, "msg": "获取信息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取信息失败"}
# if __name__ == '__main__':
#     Username="20211101052"   #借阅书籍的
#     Password="zzx021121.."
#     # Username = "20211101062"   #没借阅书籍的
#     # Password = "Das747880"
#     LG = MessageLoginPortal()   # LG login 登录
#     result = LG.login(f'{Username}', f'{Password}')
#     if result["code"] == 1000:
#         cooki = result['data']['JSESSIONID']  # 保存cookies
#         url=result['data']['URL']  #为page来省事情
#         GC = Info(cookies=cooki,url=url,User=f'{Username}',Pwd=f'{Password}')
        # GC.GetTheBalance() #获取我的卡的余额
        # GC.GetMyApply() #获取我的应用
        # GC.GetMyBooks()   #获取我的书
        # GC.GetOfficeHall() #办事大厅
        # GC.GetNewsList() #获取新闻列表
