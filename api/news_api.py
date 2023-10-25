from enum import Enum
import json
import traceback
from urllib.parse import urljoin

import requests
from requests import exceptions
from pyquery import PyQuery as pq

WSYU_BASE_URL = "http://www.wsyu.edu.cn"
# WSYU_NWXW_BASE_URL = "http://m.wsyu.edu.cn:8080"
WSYU_NWXW_BASE_URL = "http://e.wsyu.edu.cn"
TIMEOUT = 5


class IntranetNewsCatalogs(Enum):
    # 学校通知
    XXTZ = "10678"
    # 部门通知
    BMTZ = "10679"
    # 学校公文
    XXGW = "10680"
    # 教育教学
    JYJX = "10681"
    # 科研工作
    KYGZ = "10682"
    # 招生就业
    ZSJY = "10683"


class SchoolNewsCatalogs(Enum):
    # 学校要闻
    XXYW = "10307"
    # 综合新闻
    ZHXW = "10119"
    # 媒体聚焦
    MTJJ = "10120"
    # 学校荣光
    XXRG = "11656"
    # 教科成果
    JKCG = "11657"
    # 竞赛获奖
    JSHJ = "11658"
    # 优秀师生
    YXSS = "11659"
    # 视频新闻
    SPXW = "10123"


# class IntranetNews(object):
#     """内网新闻API"""
#
#     def __init__(self):
#         self.headers = requests.utils.default_headers()
#         self.headers["Referer"] = "http://www.wsyu.edu.cn"
#         self.headers[
#             "User-Agent"
#         ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
#         self.sess = requests.Session()
#         self.sess.keep_alive = False
#         self.cookies = {}
#
#     def getNewsListByCat(self, cat: str, page: int = 1):
#         """通过类型获取新闻列表"""
#         url = urljoin(WSYU_NWXW_BASE_URL, f"/ydd/notice/data?cat_id={cat}&page={page}")
#         try:
#             req_data = self.sess.get(
#                 url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
#             )
#             if req_data.status_code != 200:
#                 return {"code": 1001, "msg": "学校服务器已关闭，请早上再试试吧。", "data": {}}
#             data = req_data.json()
#             result = []
#             if data["result"] == 1:
#                 result = [
#                     {
#                         "title": i.get("title"),
#                         "date": i.get("pushTime"),
#                         "url": i.get("href")
#                     } for i in json.loads(data["msg"])
#                 ]
#             elif data["result"] == None:
#                 return {"code": 1001, "msg": "学校服务器已关闭，请早上再试试吧。", "data": []}
#             return {"code": 1000, "msg": "获取新闻列表成功", "data": result}
#         except exceptions.Timeout:
#             return {"code": 1003, "msg": "获取新闻列表超时"}
#         except Exception as e:
#             traceback.print_exc()
#             return {"code": 999, "msg": "获取新闻列表时未记录的错误：" + traceback.format_exc()}
#
#
#     def getNewsDetailByUrl(self, url:str):
#         """通过url获取新闻详情"""
#         url = urljoin(WSYU_NWXW_BASE_URL, f"/ydd/notice/dataDetail?url=http://e.wsyu.edu.cn{url}")
#         try:
#             req_data = self.sess.get(
#                 url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
#             )
#             if req_data.status_code != 200:
#                 return {"code": 1001, "msg": "学校服务器已关闭，请早上再试试吧。", "data": {}}
#             doc = pq(req_data.text, parser="html")
#             html_data = doc("body").html()
#             return {"code": 1000, "msg": "获取新闻详情成功", "data": html_data}
#         except exceptions.Timeout:
#             return {"code": 1003, "msg": "获取新闻详情超时"}
#         except Exception as e:
#             traceback.print_exc()
#             return {"code": 999, "msg": "获取新闻详情时未记录的错误：" + traceback.format_exc()}


class SchoolNews(object):
    """新闻中心API"""

    def __init__(self):
        self.headers = requests.utils.default_headers()
        self.headers["Referer"] = "http://www.wsyu.edu.cn"
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = {}

    def getNewsListByCat(self, cat: str, page: int = 1):
        """通过类型获取新闻列表"""
        url = urljoin(WSYU_BASE_URL, f"/info/iList.jsp?cat_id={cat}&cur_page={page}")
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            print(req_data.status_code)
            if req_data.status_code != 200:
                return {"code": 1001, "msg": "学校服务器已关闭，请早上再试试吧。", "data": {}}
            doc = pq(req_data.text, parser="html")
            result = []
            for li_item in doc.find('div.mainContent ul li').items():
                td_item = pq(li_item)
                item = {
                    "title": td_item.find('p.title.es a').text(),
                    "date": td_item.find('span.date').text(),
                    "url": td_item.find('p.title.es a').attr("href")
                }
                result.append(item)
            return {"code": 1000, "msg": "获取新闻列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取新闻列表超时"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取新闻列表时未记录的错误：" + traceback.format_exc()}


    def getNewsDetailByUrl(self, url:str):
        """通过url获取新闻详情"""
        url = urljoin(WSYU_BASE_URL, url)
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if req_data.status_code != 200:
                return {"code": 1001, "msg": "学校服务器已关闭，请早上再试试吧。", "data": {}}
            req_data.encoding = "utf-8"
            doc = pq(req_data.text, parser="html")
            result = {
                "title": doc("p.title").text(),
                "content": doc("div.content").html()
            }
            return {"code": 1000, "msg": "获取新闻详情成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取新闻详情超时"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取新闻详情时未记录的错误：" + traceback.format_exc()}


class IntranetNews(object):
    """内网新闻API"""

    def __init__(self):
        self.headers = requests.utils.default_headers()
        self.headers["Referer"] = "http://www.wsyu.edu.cn"
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = {}

    def getNewsListByCat(self, cat: str, page: int = 1):
        """通过类型获取新闻列表"""
        url = urljoin(WSYU_NWXW_BASE_URL, f"/info/iList.jsp?cat_id={cat}&cur_page={page}")
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if req_data.status_code != 200:
                return {"code": 1001, "msg": "学校服务器已关闭，请早上再试试吧。", "data": {}}
            doc = pq(req_data.text, parser="html")
            result = []
            for li_item in doc.find('ul.list-t li').items():
                item = {
                    "title": li_item.find('a').text(),
                    "date": li_item.find('span.date').text(),
                    "url": li_item.find('a').attr("href")
                }
                result.append(item)
            return {"code": 1000, "msg": "获取新闻列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取新闻列表超时"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取新闻列表时未记录的错误：" + traceback.format_exc()}


    def getNewsDetailByUrl(self, url:str):
        """通过url获取新闻详情"""
        url = urljoin(WSYU_NWXW_BASE_URL, url)
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if req_data.status_code != 200:
                return {"code": 1001, "msg": "学校服务器已关闭，请早上再试试吧。", "data": {}}
            req_data.encoding = "utf-8"
            doc = pq(req_data.text, parser="html")
            result = {
                "title": doc("h2.tc").text(),
                "content": doc("div.article-box").html()
            }
            return {"code": 1000, "msg": "获取新闻详情成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取新闻详情超时"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取新闻详情时未记录的错误：" + traceback.format_exc()}

if __name__ == '__main__':
    News=SchoolNews()
    t=News.getNewsListByCat('10307',1)
    print(t)