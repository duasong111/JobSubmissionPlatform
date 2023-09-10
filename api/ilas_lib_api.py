import json
#用于操作和处理文件路径
import os
#打印异常输出的自带模块
import traceback
#这个是登录的初始化的密码和哈希加密的库
import hashlib
#作用结果是拼接成一个URL
from urllib.parse import urljoin
#发送request请求
import requests
#网页解析库类似于beautifulsoul4一样的库
from pyquery import PyQuery as pq
from requests import exceptions


def loadConfig():
    with open(os.path.abspath("config.json"), mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


config = loadConfig()
BASE_URL = config["libraryBaseUrl"]
TIMEOUT = config["libraryTimeout"]


class ILasLibrary(object):
    """"图书馆查询"""

    def __init__(self):
        self.index_url = urljoin(BASE_URL, "/index.aspx")
        self.search_url = urljoin(BASE_URL, "/NTRdrBookRetr.aspx")
        self.books_local_info_url = urljoin(BASE_URL, "/GetlocalInfoAjax.aspx")
        self.headers = requests.utils.default_headers()
        self.headers["Referer"] = self.index_url
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.headers[
            "Accept"
        ] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = {}

    def search(self, pageNum, keyWords, searchType="text", sortNum=20, sortType="", sort="asc"):
        """检索书籍"""
        """
        pageNum:第几页(int)
        keyWords:搜索关键字(string)
        searchType:搜索类型(text任意词，publish出版社，subject主题词，callno索书号，isbnISBN，classno分类号，author作者，name书名)
        sortNum:每次返回多少个结果(int)
        sortType:排序方式(空为默认，selected出版日期，callno索书号，publish出版社)
        sort:排序方式(asc升序,desc降序)
        """
        try:
            search_params = {
                "page": pageNum,
                "strType": searchType,
                "strKeyValue": keyWords,
                "strpageNum": sortNum,
                "strSortType": sortType,
                "strSort": sort
            }
            # 请求检索结果
            req_search = self.sess.get(
                self.search_url,
                headers=self.headers,
                params=search_params,
                timeout=TIMEOUT
            )
            book_search_doc = pq(req_search.text, parser="html")
            search_item_list = []
            recno_list_str = ""
            for ul_item in book_search_doc.find("div.main ul.resultlist").items():
                content = pq(ul_item).find('li div.into')
                recno_list_str += pq(ul_item).find('#StrTmpRecno').attr('value') + ';'
                item = {
                    # 书籍详情url
                    'bookInfoUrl': urljoin(BASE_URL, content.find('h3.title a').attr('href')),
                    # 封面地址
                    'coverImgUrl': "http://www.bookcovers.cn/index.php?client=whzy&isbn=" + content.find(
                        'div.titbar span.dates').eq(1).find('strong').text() + "/cover",
                    # 记录号
                    'recno': pq(ul_item).find('#StrTmpRecno').attr('value'),
                    # 题名
                    'title': content.find('h3.title a').text(),
                    # 作者
                    'author': content.find('div.titbar span.author strong').text(),
                    # 出版社
                    'publisher': content.find('div.titbar span.publisher strong').text(),
                    # 出版日期
                    'publishDate': content.find('div.titbar span.dates').eq(0).find('strong').text(),
                    # ISBN
                    'ISBN': content.find('div.titbar span.dates').eq(1).find('strong').text(),
                    # 索书号
                    'callno': content.find('div.titbar span.dates').eq(2).find('strong').text(),
                    # 分类号
                    'classificationNumber': content.find('div.titbar span.dates').eq(3).find('strong').text(),
                    # 页数
                    'numberOfPages': content.find('div.titbar span.dates').eq(4).find('strong').text(),
                    # 价格
                    'price': content.find('div.titbar span.dates').eq(5).find('strong').text(),
                    # 简介
                    'briefIntroduction': content.find('div.text').text(),
                }
                # 添加到总表中
                search_item_list.append(item)
            req_books_local_info = self.sess.get(
                self.books_local_info_url,
                headers=self.headers,
                params={'ListRecno': recno_list_str},
                timeout=TIMEOUT
            )
            books_local_info_doc = pq(req_books_local_info.content)
            for index, books in enumerate(books_local_info_doc.find('books').items()):
                local_info_list = []
                for book in books.find('book').items():
                    local_info_item = {
                        'bookId': book.find('bookid').text(),
                        'barcode': book.find('barcode').text(),
                        'callno': book.find('callno').text(),
                        'localstatu': book.find('localstatu').text(),
                        'local': book.find('local').text(),
                        'cirType': book.find('cirType').text(),
                    }
                    local_info_list.append(local_info_item)
                search_item_list[index]['localInfo'] = local_info_list
            return {"code": 1000, "msg": "成功", "data": search_item_list}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "登录超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或图书馆系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "登录图书馆时未记录的错误：" + str(e)}


class IlasMyLibrary(object):
    """我的图书馆类"""

    def __init__(self):
        self.login_url = urljoin(BASE_URL, "/NTRdrLogin.aspx")
        self.index_info_url = urljoin(BASE_URL, "/MylibIndex.aspx")
        self.book_loan_url = urljoin(BASE_URL, "/NTBookLoanRetr.aspx")
        self.book_loan_result_url = urljoin(BASE_URL, "/NTBookloanResult.aspx")
        self.reader_finance_url = urljoin(BASE_URL, "/NTRdrFinRetr.aspx")
        self.headers = requests.utils.default_headers()
        self.headers["Referer"] = self.login_url
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.headers[
            "Accept"
        ] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = {}

    def login(self, username, password):
        """登录图书馆"""
        try:
            # 请求登陆
            req_before_login = self.sess.get(
                self.login_url,
                headers=self.headers,
                timeout=TIMEOUT
            )
            # 初始化登陆信息
            before_doc = pq(req_before_login.text, parser="html")
            text_viewstate = before_doc("#__VIEWSTATE").attr("value")
            text_eventvalidation = before_doc("#__EVENTVALIDATION").attr("value")
            encrypt_password = self.encoding_password('ilas' + password)
            # hhhhh=self.encoding_password("123abc456")
            # 获取相应参数后开始请求登陆
            login_data = {
                "__VIEWSTATE": text_viewstate,
                "__EVENTVALIDATION": text_eventvalidation,
                "txtName": username,
                "txtPin": encrypt_password,
                "Logintype": 'RbntRecno',
                "BtnLogin": '登 录'
            }

            req_login = self.sess.post(
                self.login_url,
                headers=self.headers,
                data=login_data,
                timeout=TIMEOUT
            )

            # print(password,encrypt_password,hhhhh)
            logged_in_doc = pq(req_login.text)
            if logged_in_doc("span#LabMessage").text() == "您还未登录，请先登录！":
                # 登录失败
                return {"code": 1001, "msg": "登录失败，原因可能是：学号错误"}
            if logged_in_doc("span#LabMessage").text() == "对不起，用户名或密码错误！":
                # 登录失败
                return {"code": 1001, "msg": "登录失败，原因可能是：密码错误"}
            # 登录成功
            self.cookies = self.sess.cookies.get_dict()
            result = {
                "studentId": username,
                "name": logged_in_doc("span#LabUserName").text(),
                "cookies": self.cookies
            }
            return {"code": 1000, "msg": "成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "登录超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或图书馆系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "登录图书馆时未记录的错误：" + str(e)}

    def loan(self, cookies):
        """查询当前借阅"""
        try:
            # 请求借阅列表
            req_loan = self.sess.get(
                self.book_loan_url,
                headers=self.headers,
                cookies=cookies,
                timeout=TIMEOUT
            )
            book_loan_doc = pq(req_loan.text, parser="html")
            if book_loan_doc("span#LabMessage").text() == "您还未登录，请先登录！":
                # 登录失败
                return {"code": 1001, "msg": "你还未登陆，可能是因为：cookies过期"}
            # 借阅图书总列表
            sub_item_list = []
            for tr_item in book_loan_doc.find('tbody tr').items():
                td_item = pq(tr_item).find('td')
                sub_item = {
                    # eq()从1开始，因为0是一个单选框
                    # 条码号
                    'barcodeNumber': td_item.eq(1).text(),
                    # 题名
                    'title': td_item.eq(2).text(),
                    # 索取号
                    'callno': td_item.eq(3).text(),
                    # 作者
                    'author': td_item.eq(4).text(),
                    # 馆藏地点
                    'collectionLocation': td_item.eq(5).text(),
                    # 借出日期
                    'lendingDate': td_item.eq(6).text(),
                    # 还回日期
                    'returnDate': td_item.eq(7).text(),
                    # 价格
                    'price': td_item.eq(8).text(),
                    # 续借次数
                    'renewalTimes': td_item.eq(9).text(),
                    # 文献流通类型
                    'circulationType': td_item.eq(10).text(),
                }
                # 添加到总表中
                sub_item_list.append(sub_item)
            return {"code": 1000, "msg": "成功", "data": sub_item_list}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "登录超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或图书馆系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "查询当前借阅时未记录的错误：" + str(e)}

    def renew(self, cookies, barcodeListStr):
        """续借图书"""
        try:
            # 请求借阅列表
            req_renew = self.sess.get(
                self.book_loan_result_url,
                headers=self.headers,
                params={'barno': barcodeListStr},
                cookies=cookies,
                timeout=TIMEOUT
            )
            book_renew_doc = pq(req_renew.text, parser="html")
            if book_renew_doc("span#LabMessage").text() == "您还未登录，请先登录！":
                # 登录失败
                return {"code": 1001, "msg": "你还未登陆，可能是因为：cookies过期"}
            # 借阅图书总列表
            sub_item_list = []
            for tr_item in book_renew_doc.find('tbody tr').items():
                td_item = pq(tr_item).find('td')
                sub_item = {
                    'barcodeStatus': td_item.eq(0).find('b font').text(),
                    # 条码号
                    'barcodeName': td_item.eq(1).text(),
                    # 题名
                    'title': td_item.eq(2).text(),
                    # 索取号
                    'callno': td_item.eq(3).text(),
                    # 作者
                    'author': td_item.eq(4).text(),
                    # 馆藏地点
                    'collectionLocation': td_item.eq(5).text(),
                    # 借出日期
                    'lendingDate': td_item.eq(6).text(),
                    # 还回日期
                    'returnDate': td_item.eq(7).text(),
                    # 价格
                    'price': td_item.eq(8).text(),
                    # 续借次数
                    'renewalTimes': td_item.eq(9).text(),
                    # 文献流通类型
                    'circulationType': td_item.eq(10).text(),
                }
                # 添加到总表中
                sub_item_list.append(sub_item)
            return {"code": 1000, "msg": "成功", "data": sub_item_list}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "登录超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或图书馆系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "登录图书馆时未记录的错误：" + str(e)}

    def fin(self, cookies):
        """读者财经情况"""
        try:
            # 请求借阅列表
            req_fin = self.sess.get(
                self.reader_finance_url,
                headers=self.headers,
                cookies=cookies,
                timeout=TIMEOUT
            )
            reader_fin_doc = pq(req_fin.text, parser="html")
            if reader_fin_doc("span#LabMessage").text() == "您还未登录，请先登录！":
                # 登录失败
                return {"code": 1001, "msg": "你还未登陆，可能是因为：cookies过期"}
            fin_result = {
                "ordinaryBorrowingDeposit": reader_fin_doc('span#labCW').text(),
                "specialBorrowingDeposit": reader_fin_doc('span#labCZ').text(),
                "cashAdvancePaymentAmount": reader_fin_doc('span#labYY').text(),
                "ordinaryLoanArrears": reader_fin_doc('span#labFW').text(),
                "specialLoanArrears": reader_fin_doc('span#labFZ').text(),
            }
            return {"code": 1000, "msg": "成功", "data": fin_result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "登录超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或图书馆系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "登录图书馆时未记录的错误：" + str(e)}

    @staticmethod
    def encoding_password(str):
        return hashlib.md5(str.encode(encoding='utf-8')).hexdigest()

"""用于登录测试"""
if __name__ == '__main__':
    ilas_my_lib = IlasMyLibrary()
    login_result = ilas_my_lib.login("20201101381", "02203117")
#     print(login_result)
#     loan_result = ilas_my_lib.loan(login_result['data']['cookies'])
#     print(loan_result)
#     renew_result = ilas_my_lib.renew(login_result['data']['cookies'], ['A1379582'])
#     print(renew_result)
#     fin_result = ilas_my_lib.fin(login_result['data']['cookies'])
#     print(fin_result)
#     ilas_lib = ILasLibrary()
#     search_result = ilas_lib.search(1, "逆向分析")
#     print(search_result)
