import traceback
from urllib.parse import urljoin

import requests
from requests import exceptions
from pyquery import PyQuery as pq

BING_BASE_URL = "https://cn.bing.com"
TIMEOUT = 5
class Bing(object):
    """必应api"""

    def __init__(self):
        self.headers = requests.utils.default_headers()
        self.headers["Referer"] = "https://cn.bing.com"
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = {}

    def getDailyPic(self, day=0):
        """获取每日背景图"""
        url = urljoin(BING_BASE_URL, f"/HPImageArchive.aspx?format=js&idx={day}&n=1&mkt=zh-CN")
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            data = req_data.json()
            result = {
                "title": data["images"][0]["title"],
                "copyright": data["images"][0]["copyright"],
                "url": urljoin(BING_BASE_URL, data["images"][0]["url"]),
                "startDate": data["images"][0]["startdate"],
                "endDate": data["images"][0]["enddate"],
            }
            return {"code": 1000, "msg": "获取每日图片成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取每日图片超时"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取每日图片时未记录的错误：" + traceback.format_exc()}

# if __name__ == '__main__':
#     picture= Bing()
#     result=picture.getDailyPic()
#     print(result)
