import base64
import binascii
import datetime
import json
import re
import os
import time
import traceback
from pprint import pprint
from urllib.parse import urljoin

import requests
import rsa
from pyquery import PyQuery as pq
from requests import exceptions


# def loadConfig():
#     with open(os.path.abspath("config.json"), mode='r', encoding='utf-8') as f:
#         return json.loads(f.read())


# config = loadConfig()
BASE_URL = 'http://syjw.wsyu.edu.cn'
TIMEOUT = 4


class Login(object):
    """登录类"""

    def __init__(self, cookies={}):
        self.login_url_nodomain = "/xtgl/login_slogin.html"
        self.key_url = urljoin(BASE_URL, "/xtgl/login_getPublicKey.html") #开始登录进入的网址
        self.login_url = urljoin(BASE_URL, "/xtgl/login_slogin.html")
        self.index_menu_url = urljoin(BASE_URL, "/xtgl/index_initMenu.html")#登录成功的网址
        self.index_user_info = urljoin(BASE_URL, "/xtgl/index_cxYhxxIndex.html?xt=jw&localeKey=zh_CN&gnmkdm=index")
        self.login_switch_users_xs_url = urljoin(BASE_URL, "/xtgl/index_initMenu.html?jsdm=xs")
        self.login_switch_users_js_url = urljoin(BASE_URL, "/xtgl/index_initMenu.html?jsdm=js")
        self.login_forward_url = urljoin(BASE_URL, "/xtgl/dl_loginForward.html")
        self.check_password_url = urljoin(BASE_URL, "/xtgl/mmgl_cxCheckRsaYhMm.html")
        self.submit_reset_password_url = urljoin(BASE_URL, "/xtgl/mmgl_xgRsaMm.html")
        self.kaptcha_url = urljoin(BASE_URL, "/kaptcha")
        self.headers = requests.utils.default_headers()
        self.headers["Host"] = "syjw.wsyu.edu.cn"
        self.headers["Origin"] = "http://syjw.wsyu.edu.cn"
        self.headers["Referer"] = self.login_url
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.headers[
            "Accept"
        ] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.req = ""
        self.cookies = cookies
        self.require_change_password = False
        self.is_zsb = False
        self.is_fdy = False

    def login(self, sid, password):
        """登录教务系统"""
        try:
            # 登录页
            req_csrf = self.sess.get(
                self.login_url, headers=self.headers, timeout=TIMEOUT
            )
            # 获取csrf_token
            doc = pq(req_csrf.text)
            csrf_token = doc("#csrftoken").attr("value")
            pre_cookies = self.sess.cookies.get_dict()
            # 获取publicKey并加密密码
            req_pubkey = self.sess.get(
                self.key_url, headers=self.headers, timeout=TIMEOUT
            ).json()
            modulus = req_pubkey["modulus"]
            exponent = req_pubkey["exponent"]
            if str(doc("input#yzm")) != "":
                # 有验证码
                try:
                    req_kaptcha = self.sess.get(
                        self.kaptcha_url, headers=self.headers, timeout=TIMEOUT
                    )
                    kaptcha_pic = base64.b64encode(req_kaptcha.content).decode()
                    return {
                        "code": 1001,
                        "msg": "获取验证码成功",
                        "data": {
                            "sid": sid,
                            "csrf_token": csrf_token,
                            "cookies": pre_cookies,
                            # "password": password,
                            "modulus": modulus,
                            "exponent": exponent,
                            "kaptcha_pic": kaptcha_pic,
                            "timestamp": time.time()
                        },
                    }
                except exceptions.Timeout:
                    return {"code": 1003, "msg": "获取验证码超时"}
                except exceptions.RequestException:
                    traceback.print_exc()
                    return {"code": 2333, "msg": "请重试或教务系统维护中"}
                except Exception as e:
                    traceback.print_exc()
                    return {"code": 999, "msg": "获取验证码时未记录的错误：" + traceback.format_exc()}
            else:
                # 无验证码
                encrypt_password = self.encryptPassword(
                    password, modulus, exponent
                )
                # 登录数据
                login_data = {
                    "csrftoken": csrf_token,
                    "yhm": sid,
                    "mm": encrypt_password,
                }
                # 请求登录
                self.req = self.sess.post(
                    self.login_url,
                    headers=self.headers,
                    data=login_data,
                    timeout=TIMEOUT,
                )
                # 判断是否登陆失败
                doc = pq(self.req.text)
                tips = doc("p#tips")
                # 判断登陆后的状态，比如密码不对或者账号未注册
                if str(tips) != "":
                    if "用户名或密码" in tips.text():
                        return {"code": 1002, "msg": "用户名或密码不正确"}
                    else:
                        return {"code": 998, "msg": tips.text()}
                # 判断是否需要重置密码
                alert = doc("h4.alert-heading")
                if str(alert) != "" and "请重置密码" in alert.text():
                    self.require_change_password = True
                # 登陆成功后执行操作
                self.cookies = self.sess.cookies.get_dict()
                # 获取账户默认登陆类型
                login_forward_req = self.sess.get(
                    self.login_forward_url,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=TIMEOUT
                )
                # 判断是否专升本学生
                if len(sid) == 11 and "jsdm=zsb" in login_forward_req.url:
                    self.is_zsb = True
                    # 若为专升本学生，需要先切换用户，请求一个地址即可
                    # 但是教师账号不能请求该地址，需要做学号的长度判断
                    self.sess.get(
                        self.login_switch_users_xs_url,
                        headers=self.headers,
                        cookies=self.cookies,
                        timeout=TIMEOUT,
                    )
                    # 若为专升本学生，需强制改密码，其他可以暂时跳过
                # 判断是否辅导员
                if len(sid) == 10 and "jsdm=fdy" in login_forward_req.url:
                    self.is_fdy = True
                    self.sess.get(
                        self.login_switch_users_js_url,
                        headers=self.headers,
                        cookies=self.cookies,
                        timeout=TIMEOUT
                    )
                    # return {"code": 1004,
                    #         "msg": "目前仅支持学生与教师登陆，暂不支持辅导员登陆，若有相关需求可联系开发者。"}
                # # 判断是否存在时盒信息
                # shiHe = self.sess.get(
                #     self.index_user_info,
                #     headers=self.headers,
                #     cookies=self.cookies,
                #     timeout=TIMEOUT,
                # )
                # docShiHe = pq(shiHe.text)
                # if "当前学年学期无学生时盒数据" in docShiHe.text():
                #     return {"code": 1005, "msg": "当前学年学期无学生时盒数据，请稍后再试或联系教务管理员"}
                # 成功
                result = {
                    "code": 1000,
                    "msg": "登陆成功",
                    "data": {
                        "cookies": self.cookies,
                        "changePass": 0
                    }
                }
                if self.require_change_password:
                    result["code"] = 1101
                    result["msg"] = "登陆成功，但需要改密码"
                    result["data"]["changePass"] = 1
                if self.is_zsb and self.require_change_password:
                    result["code"] = 1102
                    result["msg"] = "登陆失败，专升本学生必须修改密码后登陆"
                    result["data"]["changePass"] = 2
                return result
        except exceptions.Timeout:
            return {"code": 1003, "msg": "登录超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "登录时未记录的错误：" + traceback.format_exc()}

    def loginWithKaptcha(
            self, sid, csrf_token, password, modulus, exponent, kaptcha
    ):
        """需要验证码的登陆"""
        try:
            encrypt_password = self.encryptPassword(password, modulus, exponent)
            login_data = {
                "csrftoken": csrf_token,
                "yhm": sid,
                "mm": encrypt_password,
                "yzm": kaptcha,
            }
            self.req = self.sess.post(
                self.login_url,
                headers=self.headers,
                cookies=self.cookies,
                data=login_data,
                timeout=TIMEOUT,
            )
            # 请求登录
            doc = pq(self.req.text)
            tips = doc("p#tips")
            if str(tips) != "":
                if "验证码" in tips.text():
                    return {"code": 1004, "msg": "验证码输入错误"}
                elif "用户名或密码" in tips.text():
                    return {"code": 1002, "msg": "用户名或密码不正确"}
                else:
                    return {"code": 998, "msg": tips.text()}
            self.cookies = self.sess.cookies.get_dict()
            return {"code": 1000, "msg": "登录成功", "data": self.cookies}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "登录超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "验证码登录时未记录的错误：" + traceback.format_exc()}

    def forceResetPasswordDesc(self):
        """获取登陆时强制重置密码的描述信息"""
        try:
            self.req = self.sess.post(
                self.index_menu_url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in self.req.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(self.req.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            # if self.req.status_code == 302:
            #     return {"code": 1004, "msg": "登陆过期，请重新登录"}
            # 判断是否需要重置密码
            alert = doc("h4.alert-heading")
            if str(alert) != "" and "请重置密码" in alert.text():
                data = {
                    "id": doc("input#yhm").attr("value"),
                    "name": doc("input.form-control").eq(0).attr("value"),
                    "desc": "根据教务要求，您需要按照下方要求修改您的密码：",
                    # 为了保留换行符，此处采用.html()
                    "content": doc("pre.alert-warning").html(),
                    "jwPasswordConfig": {
                        "yhm": doc("input#yhm").attr("value"),
                        "sessionUserKey": doc("input#sessionUserKey").attr("value"),
                        "sfcyxmmkl": doc("input#sfcyxmmkl").attr("value"),
                        "min": doc("input#min").attr("value"),
                        "max": doc("input#max").attr("value")
                    }
                }
                return {"code": 1000, "msg": "获取重置密码描述信息成功", "data": data}
            else:
                return {"code": 1100, "msg": "您的账号不需要改密码"}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取重置密码描述信息超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取重置密码描述信息时未记录的错误：" + traceback.format_exc()}

    def checkPasswordCorrectness(self, password: str, is_force: bool = True):
        """检查密码对不对"""
        try:
            # 获取publicKey并加密密码
            req_pubkey = self.sess.get(
                "%s%s" % (self.key_url, "" if is_force else "?gnmkdm=index"),
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT
            ).json()
            modulus = req_pubkey["modulus"]
            exponent = req_pubkey["exponent"]
            encrypt_old_password = self.encryptPassword(
                password, modulus, exponent
            )
            # 提交表单数据
            submit_data = {
                "kl": encrypt_old_password,
            }
            submit_req = self.sess.post(
                "%s%s" % (self.check_password_url, "" if is_force else "?gnmkdm=index"),
                headers=self.headers,
                cookies=self.cookies,
                data=submit_data,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in submit_req.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            submit_req = submit_req.json()
            if submit_req:
                return {"code": 1000, "msg": "原密码正确", "data": {"result": submit_req}}
            else:
                return {"code": 1002, "msg": "原密码错误", "data": {"result": submit_req}}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "修改密码超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "修改密码时未记录的错误：" + traceback.format_exc()}

    def resetPassword(self, old_password: str, new_password: str, is_force: bool = True):
        """重置密码"""
        try:
            # 获取publicKey并加密密码
            req_pubkey = self.sess.get(
                "%s%s" % (self.key_url, "" if is_force else "?gnmkdm=index"),
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT
            ).json()
            modulus = req_pubkey["modulus"]
            exponent = req_pubkey["exponent"]
            encrypt_old_password = self.encryptPassword(
                old_password, modulus, exponent
            )
            encrypt_new_password = self.encryptPassword(
                new_password, modulus, exponent
            )
            # 提交表单数据
            submit_data = {
                "ymm": encrypt_old_password,
                "mm": encrypt_new_password,
                "doType": "save"
            }
            submit_req = self.sess.post(
                "%s%s" % (self.submit_reset_password_url, "" if is_force else "?gnmkdm=index"),
                headers=self.headers,
                cookies=self.cookies,
                data=submit_data,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in submit_req.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            if "修改成功" in submit_req.text:
                return {"code": 1000, "msg": "修改密码成功", "data": {"result": True, "text": submit_req.text}}
            elif "用户登录" in submit_req.text:
                return {"code": 1004, "msg": "登陆过期了，重新登录试试？",
                        "data": {"result": False, "text": submit_req.text}}
            else:
                return {"code": 1005, "msg": f'修改密码失败，原因为:[{submit_req.text}]',
                        "data": {"result": False, "text": submit_req.text}}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "修改密码超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "修改密码时未记录的错误：" + traceback.format_exc()}

    @classmethod
    def encryptPassword(cls, pwd, n, e):
        """对密码base64编码和rsa加密"""
        message = str(pwd).encode()
        rsa_n = binascii.b2a_hex(binascii.a2b_base64(n))
        rsa_e = binascii.b2a_hex(binascii.a2b_base64(e))
        key = rsa.PublicKey(int(rsa_n, 16), int(rsa_e, 16))
        encropy_pwd = rsa.encrypt(message, key)
        result = binascii.b2a_base64(encropy_pwd)
        return result


class Info(object):
    """获取信息类"""

    def __init__(self, cookies, is_teacher=False):
        self.login_url_nodomain = "/xtgl/login_slogin.html"
        self.headers = requests.utils.default_headers()
        self.headers["Referer"] = BASE_URL
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = cookies
        self.is_teacher = is_teacher

    def getTeacherPersonInfo(self):
        """获取教师信息"""
        url = urljoin(BASE_URL, "/jsxx/jsgrxx_cxJsgrxx.html?gnmkdm=N1585")
        try:
            req_info = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_info.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(req_info.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            pending_result = {}
            # 教师基本信息
            for ul_item in doc.find("div#home div.row div.col-md-8.col-sm-8 div.row div.col-md-6.col-sm-6").items():
                content = pq(ul_item).find('div.form-group')
                key = pq(content).find('label.col-sm-4.col-xs-4.control-label').text()
                value = pq(content).find('div.col-sm-8.col-xs-8 p.form-control-static').text()
                # 到这一步，解析到的数据基本就是一个键值对形式的html数据了，比如"教工号：123456"
                pending_result[key] = value
            # 教师时盒信息
            for ul_item in doc.find("div#profile div div.row div.col-md-4.col-sm-4").items():
                content = pq(ul_item).find('div.form-group')
                key = pq(content).find('label.col-sm-4.col-xs-4.control-label').text()
                value = pq(content).find('div.col-sm-8.col-xs-8 p.form-control-static').text()
                # 到这一步，解析到的数据基本就是一个键值对形式的html数据了，比如"教工号：123456"
                pending_result[key] = value
            # 教师通讯信息
            for ul_item in doc.find("div#info div div.row div.col-md-4.col-sm-4").items():
                content = pq(ul_item).find('div.form-group')
                key = pq(content).find('label.col-sm-4.col-xs-4.control-label').text()
                value = pq(content).find('div.col-sm-8.col-xs-8 p.form-control-static').text()
                # 到这一步，解析到的数据基本就是一个键值对形式的html数据了，比如"教工号：123456"
                pending_result[key] = value
            result = {
                "teacherId": pending_result["教工号"],
                "name": pending_result["姓名"],
                "sex": "未知" if pending_result.get("性别") is None else pending_result["性别"],
                "idNumber": 0 if pending_result.get("身份证号") is None else pending_result["身份证号"],
                "collegeName": "无" if pending_result.get("任职部门") is None else pending_result["任职部门"],
                "phoneNumber": "无" if pending_result.get("手机号码") is None else pending_result["手机号码"],
            }
            return {"code": 1000, "msg": "获取教师信息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取教师信息超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取教师信息时未记录的错误：" + traceback.format_exc()}

    def getPersonInfo(self):
        """获取个人信息"""
        url = urljoin(BASE_URL, "/xsxxxggl/xsgrxxwh_cxXsgrxx.html?gnmkdm=N100801")
        try:
            req_info = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_info.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(req_info.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            pending_result = {}
            # 学生基本信息
            for ul_item in doc.find("div.row div.col-sm-6").items():
                content = pq(ul_item).find('div.form-group')
                key = pq(content).find('label.col-sm-4.control-label').text()
                value = pq(content).find('div.col-sm-8 p.form-control-static').text()
                # 到这一步，解析到的数据基本就是一个键值对形式的html数据了，比如"学号：123456"
                pending_result[key] = value
            # 学生学籍信息，其他信息，联系方式
            for ul_item in doc.find("div.row div.col-sm-4").items():
                content = pq(ul_item).find('div.form-group')
                key = pq(content).find('label.col-sm-4.control-label').text()
                value = pq(content).find('div.col-sm-8 p.form-control-static').text()
                # 到这一步，解析到的数据基本就是一个键值对形式的html数据了，比如"学号：123456"
                pending_result[key] = value
            if pending_result["学号："] == '':
                return {"code": 1014, "msg": "当前学年学期无学生时盒数据，您可能已经毕业了，祝前程似锦～\n\n如果是专升本同学，请使用专升本后的新学号登录哈～"}
            result = {
                "studentId": pending_result["学号："],
                "name": pending_result["姓名："],
                "birthDay": "无" if pending_result.get("出生日期：") == '' else pending_result["出生日期："],
                "idNumber": "无" if pending_result.get("证件号码：") == '' else pending_result["证件号码："],
                "candidateNumber": "无" if pending_result.get("考生号：") == '' else pending_result["考生号："],
                "status": "无" if pending_result.get("学籍状态：") == '' else pending_result["学籍状态："],
                "collegeName": "无" if pending_result.get("学院名称：") == '' else pending_result["学院名称："],
                "majorName": "无" if pending_result.get("专业名称：") == '' else pending_result["专业名称："],
                "className": "无" if pending_result.get("班级名称：") == '' else pending_result["班级名称："],
                "entryDate": "无" if pending_result.get("入学日期：") == '' else pending_result["入学日期："],
                "graduationSchool": "无" if pending_result.get("毕业中学：") == '' else pending_result["毕业中学："],
                "domicile": "无" if pending_result.get("籍贯：") == '' else pending_result["籍贯："],
                "phoneNumber": "无" if pending_result.get("手机号码：") == '' else pending_result["手机号码："],
                "parentsNumber": "无",
                "email": "无" if pending_result.get("电子邮箱：") == '' else pending_result["电子邮箱："],
                "politicalStatus": "无" if pending_result.get("政治面貌：") == '' else pending_result["政治面貌："],
                "national": "无" if pending_result.get("民族：") == '' else pending_result["民族："],
                "education": "无" if pending_result.get("培养层次：") == '' else pending_result["培养层次："],
                "postalCode": "无" if pending_result.get("邮政编码：") == '' else pending_result["邮政编码："],
                "grade": int(pending_result["学号："][0:4]),
            }
            return {"code": 1000, "msg": "获取个人信息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取个人信息超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取个人信息时未记录的错误：" + traceback.format_exc()}

    def getTeacherExamInfo(self, year, term):
        """获取任课教师考试信息"""
        url = urljoin(BASE_URL, "/kwgl/rkjskscx_cxRkjsksIndex.html?doType=query&gnmkdm=N358126")
        dict = {"1": "3", "2": "12", "0": ""}  # 修改检测学期
        if dict.get(term) is not None:
            term = dict.get(term)
        else:
            return {"code": 1006, "msg": "错误的学期编号：" + str(term)}
        data = {
            "xnm": year,  # 学年数
            "xqm": term,  # 学期数，第一学期为3，第二学期为12, 整个学年为空''
            "ksmcdmb_id": "",
            "ksrq": "",
            "sjbh": "",
            "kc": "",
            "jkjs": "",
            "kch": "",
            "_search": "false",
            "nd": int(time.time() * 1000),
            "queryModel.showCount": "200",  # 每页最多条数
            "queryModel.currentPage": "1",
            "queryModel.sortName": "kssj",
            "queryModel.sortOrder": "asc",
            "time": "0",  # 查询次数
        }
        try:
            req_exam_info = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_exam_info.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_exam_info.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            exam_info = req_exam_info.json()
            if exam_info.get("items"):  # 防止数据出错items为空
                result = {
                    "teacherInfo": exam_info["items"][0]["jsxm"],
                    "schoolYear": exam_info["items"][0]["xnm"],
                    "schoolTerm": exam_info["items"][0]["xqmmc"],
                    "examInfo": [
                        {
                            "courseTitle": i.get("kcmc"),
                            "teacher": i.get("jsxm"),
                            "examName": i.get("sjbh"),
                            "examCampus": "无" if i.get("xqmc") is None else i["xqmc"],
                            "examPosition": "无" if i.get("cdmc") is None else i["cdmc"],
                            "examTimeText": "无" if i.get("kssj") is None else i["kssj"],
                            "examWeek": re.findall(r"(?<=第).[0-9]*?(?=周)", i["kssj"])[0],
                            "examWeekDay": re.findall(r"(?<=周周).[0-9]*?", i["kssj"])[0],
                            "examDate": re.findall(r"\d{4}-\d{1,2}-\d{1,2}", i["kssj"])[0],
                            "examTime": re.findall(r"\d{1,2}:\d{1,2}-\d{1,2}:\d{1,2}", i["kssj"])[0],
                        } for i in exam_info.get("items")
                    ],
                }
                return {"code": 1000, "msg": "获取考试信息成功", "data": result}
            else:
                result = {
                    "name": "",
                    "studentId": "",
                    "schoolYear": "",
                    "schoolTerm": "",
                    "examInfo": [],
                }
                return {"code": 1005, "msg": "获取内容为空", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取成绩超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取考试信息时未记录的错误：" + traceback.format_exc()}

    def getExamInfo(self, year, term):
        """获取考试信息"""
        url = urljoin(BASE_URL, "/kwgl/kscx_cxXsksxxIndex.html?doType=query&gnmkdm=N358105")
        dict = {"1": "3", "2": "12", "0": ""}  # 修改检测学期
        if dict.get(term) is not None:
            term = dict.get(term)
        else:
            return {"code": 1006, "msg": "错误的学期编号：" + str(term)}
        data = {
            "xnm": year,  # 学年数
            "xqm": term,  # 学期数，第一学期为3，第二学期为12, 整个学年为空''
            "_search": "false",
            "nd": int(time.time() * 1000),
            "queryModel.showCount": "100",  # 每页最多条数
            "queryModel.currentPage": "1",
            "queryModel.sortName": "",
            "queryModel.sortOrder": "asc",
            "time": "0",  # 查询次数
        }
        try:
            req_exam_info = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_exam_info.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_exam_info.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            exam_info = req_exam_info.json()
            if exam_info.get("items"):  # 防止数据出错items为空
                result = {
                    "name": exam_info["items"][0]["xm"],
                    "studentId": exam_info["items"][0]["xh"],
                    "schoolYear": exam_info["items"][0]["xnm"],
                    "schoolTerm": exam_info["items"][0]["xqmmc"],
                    "examInfo": [
                        {
                            "courseTitle": i.get("kcmc"),
                            "teacher": i.get("jsxx"),
                            "courseId": i.get("kch"),
                            "examName": i.get("ksmc"),
                            "examCampus": "无" if i.get("cdxqmc") is None else i["cdxqmc"],
                            "examPosition": "无" if i.get("cdmc") is None else i["cdmc"],
                            "examTimeText": "无" if i.get("kssj") is None else i["kssj"],
                            # "includeTime": re.findall(r"第\d{1,2}周|周\d{1,2}|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}:\d{1,2}-\d{1,2}:\d{1,2}", i["kssj"]),
                            "examWeek": re.findall(r"(?<=第).[0-9]*?(?=周)", i["kssj"])[0],
                            "examWeekDay": re.findall(r"(?<=周周).[0-9]*?", i["kssj"])[0],
                            "examDate": re.findall(r"\d{4}-\d{1,2}-\d{1,2}", i["kssj"])[0],
                            "examTime": re.findall(r"\d{1,2}:\d{1,2}-\d{1,2}:\d{1,2}", i["kssj"])[0],
                        } for i in exam_info.get("items")
                    ],
                }
                return {"code": 1000, "msg": "获取考试信息成功", "data": result}
            else:
                result = {
                    "name": "",
                    "studentId": "",
                    "schoolYear": "",
                    "schoolTerm": "",
                    "examInfo": [],
                }
                return {"code": 1005, "msg": "获取内容为空", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取成绩超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取考试信息时未记录的错误：" + traceback.format_exc()}

    def getGrade(self, year, term):
        """获取成绩"""
        url = urljoin(BASE_URL, "/cjcx/cjcx_cxDgXscj.html?doType=query&gnmkdm=N305005")
        dict = {"1": "3", "2": "12", "0": ""}  # 修改检测学期
        if dict.get(term) is not None:
            term = dict.get(term)
        else:
            return {"code": 1006, "msg": "错误的学期编号：" + str(term)}
        data = {
            "xnm": year,  # 学年数
            "xqm": term,  # 学期数，第一学期为3，第二学期为12, 整个学年为空''
            "_search": "false",
            "nd": int(time.time() * 1000),
            "queryModel.showCount": "100",  # 每页最多条数
            "queryModel.currentPage": "1",
            "queryModel.sortName": "",
            "queryModel.sortOrder": "asc",
            "time": "0",  # 查询次数
        }
        try:
            req_grade = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_grade.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_grade.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            grade = req_grade.json()
            if grade.get("items"):  # 防止数据出错items为空
                # 课程成绩列表
                course_list = []
                # 算术平均分
                ari_ave = 0
                # 加权平均分
                wei_ave = 0
                # 学分绩点
                gpa = 0
                # 学分和
                credit_sum = 0
                # 参与计算的成绩总数
                course_count = 0
                for i in grade.get("items"):
                    # 处理成绩列表
                    item = {
                        "courseTitle": i.get("kcmc"),
                        "teacher": i.get("jsxm"),
                        "courseId": i.get("kch_id"),
                        "classId": "无" if i.get("jxb_id") is None else i["jxb_id"],
                        "className": "无" if i.get("jxbmc") is None else i["jxbmc"],
                        "courseNature": "无" if i.get("kcxzmc") is None else i["kcxzmc"],
                        "credit": "无" if i.get("xf") is None else format(float(i["xf"]), ".1f"),
                        "grade": i.get("bfzcj") if i.get("bfzcj") is not None else i["cj"],
                        "gradePoint": " " if i.get("jd") is None else format(float(i["jd"]), ".1f"),
                        "gradeNature": i.get("ksxz"),
                        "startCollege": "无" if i.get("kkbmmc") is None else i["kkbmmc"],
                        "courseMark": i.get("kcbj"),
                        "courseCategory": "无" if i.get("kclbmc") is None else i["kclbmc"],
                        "courseAttribution": "无" if i.get("kcgsmc") is None else i["kcgsmc"],
                    }
                    course_list.append(item)
                    # 防止成绩，学分等数据为"无"，此处进行捕获异常
                    # 计算成绩
                    if item.get("gradeNature").find("正常考试") != -1 and item.get("courseNature").find(
                            "公共选修") == -1:
                        try:
                            i_ari_ave = float(item.get("grade"))
                            i_wei_ave = float(item.get("grade")) * float(item.get("credit"))
                            i_gpa = float(item.get("gradePoint")) * float(item.get("credit"))
                            i_credit_sum = float(item.get("credit"))
                        except Exception as e:
                            traceback.print_exc()
                            continue
                        else:
                            ari_ave += i_ari_ave
                            wei_ave += i_wei_ave
                            gpa += i_gpa
                            credit_sum += i_credit_sum
                            course_count += 1
                if course_count != 0 and credit_sum != 0:
                    ari_ave = ari_ave / course_count
                    wei_ave = wei_ave / credit_sum
                    gpa = gpa / credit_sum
                result = {
                    "name": grade["items"][0]["xm"],
                    "studentId": grade["items"][0]["xh"],
                    "schoolYear": grade["items"][0]["xnm"],
                    "schoolTerm": grade["items"][0]["xqmmc"],
                    # 算术平均分
                    "arithmeticalAverage": round(ari_ave, 2),
                    # 加权平均分
                    "weightedAverage": round(wei_ave, 2),
                    # 学分绩点
                    "gpa": round(gpa, 2),
                    # 课程成就
                    "course": course_list,
                }
                return {"code": 1000, "msg": "获取成绩成功", "data": result}
            else:
                result = {
                    "name": "",
                    "studentId": "",
                    "schoolYear": "",
                    "schoolTerm": "",
                    "gpa": 0.0,
                    "course": [],
                }
                return {"code": 1005, "msg": "获取内容为空", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取成绩超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取成绩时未记录的错误：" + traceback.format_exc()}

    def getGradeDetail(self, year, term, class_id, course_name):
        """获取成绩详情"""
        url = urljoin(BASE_URL, "/cjcx/cjcx_cxCjxqGjh.html?gnmkdm=N305005")
        term = int(term) * int(term) * 3
        data = {
            "xnm": year,
            "xqm": term,
            "jxb_id": class_id,
            "kcmc": course_name
        }
        try:
            req_grade_detail = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_grade_detail.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(req_grade_detail.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            sub_item_list = []
            # 遍历tbody中的tr标签
            for td in doc('tbody').find('tr'):
                sub_item = {
                    # 成绩分项（第一列）,同时去除两边括号和空格
                    'name': pq(td).find('td').eq(0).text().strip('【 】'),
                    # 成绩分项比例（第二列）
                    'percent': pq(td).find('td').eq(1).text(),
                    # 成绩（第三列）
                    'score': pq(td).find('td').eq(2).text()
                }
                # 添加到总表中
                sub_item_list.append(sub_item)
            if len(sub_item_list) != 0:  # 防止数据出错list为空
                result = {
                    "courseName": course_name,
                    "courseDetail": [
                        {
                            "name": "无" if i.get("name") is None else i["name"],
                            "percent": "无" if i.get("percent") is None else i["percent"],
                            "score": "无" if i.get("score") is None else i["score"],
                        } for i in sub_item_list
                    ],
                }
                return {"code": 1000, "msg": "获取成绩成功", "data": result}
            else:
                return {"code": 1005, "msg": "获取内容为空"}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取成绩超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取成绩时未记录的错误：" + traceback.format_exc()}

    def getTeacherSchedule(self, year, term):
        """获取教师课程表信息"""
        url = urljoin(BASE_URL, "/kbcx/jskbcx_cxJsKb1.html?gnmkdm=N2150")
        dict = {"1": "3", "2": "12"}
        if dict.get(term) is not None:
            term = dict.get(term)
        else:
            return {"code": 1006, "msg": "错误的学期编号：" + str(term)}
        data = {
            "xnm": year,
            "xqm": term,
            "kzlx": "ck",
            "djsktkb": 0
        }
        try:
            req_schedule = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_schedule.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_schedule.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            schedule = req_schedule.json()
            result = {
                "name": schedule["jsxx"]["XM"],
                "teacherId": schedule["jsxx"]["JGH"],
                "schoolYear": schedule["jsxx"]["XNM"],
                "schoolTerm": schedule["jsxx"]["XQMMC"],
                "normalCourse": [
                    {
                        "courseTitle": i.get("kcmc"),
                        'courseTitleShort': i.get('kcmc')[0:9] + '..' if len(i.get('kcmc')) > 9 else i.get('kcmc'),
                        "teacher": "无" if i.get("jsxm") is None else i["jsxm"],
                        "courseId": i.get("kch"),
                        "courseWeekday": i.get("xqj"),
                        "courseSection": i.get("jc"),
                        "courseSectionStart": self.getCourseSectionStart(re.findall(r"(\d+)", i["jc"])),
                        "courseSectionContinue": self.getCourseSectionContinue(re.findall(r"(\d+)", i["jc"])),
                        "includeSection": self.listTime(re.findall(r"(\d+)", i["jc"])),
                        # "upTime": self.upTime(re.findall(r"(\d+)", i["jc"])),
                        # "courseTime": self.calTime(re.findall(r"(\d+)", i["jc"])),
                        "courseWeek": i.get("zcd"),
                        "includeWeeks": self.calWeeks(re.findall(r"[^,]+", i["zcd"])),
                        "exam": i.get("khfsmc"),
                        "campus": i.get("xqmc"),
                        "courseRoom": i.get("cdmc"),
                        "courseRoomShort": self.subCourseRoomStr(str(i.get("cdmc"))),
                        "className": i.get("jxbmc"),
                        "classComposition": i.get("jxbzc"),
                        "hoursComposition": i.get("kcxszc"),
                        "weeklyHours": i.get("zhxs"),
                        "totalHours": i.get("zxs"),
                        "credit": "0.0" if i.get("xf") == "无" else format(float(i.get("xf")), ".1f"),
                    }
                    for i in schedule["kbList"]
                ],
                "otherCourse": [{
                    'courseTitle': i.get('qtkcgs').split('/')[0],
                    'courseWeek': i.get('qtkcgs').split('/')[1],
                    'courseClass': i.get('qtkcgs').split('/')[3],
                    'courseText': i.get('qtkcgs')
                } for i in schedule['sjkList']]
            }
            """
                处理同周同天同课程不同时段合并显示的问题
            """
            repetIndex = []
            count = 0
            for items in result["normalCourse"]:
                for index in range(len(result["normalCourse"])):
                    if (result["normalCourse"]).index(items) == count:  # 如果对比到自己就忽略
                        pass
                    elif (
                            items["courseTitle"]
                            == result["normalCourse"][index]["courseTitle"]  # 同周同天同课程
                            and items["courseWeekday"]
                            == result["normalCourse"][index]["courseWeekday"]
                            and items["courseWeek"]
                            == result["normalCourse"][index]["courseWeek"]
                    ):
                        repetIndex.append(index)  # 满足条件记录索引
                    else:
                        pass
                count = count + 1  # 记录当前对比课程的索引
            if len(repetIndex) % 2 != 0:  # 暂时考虑一天两个时段上同一门课，不满足条件不进行修改
                return {"code": 1000, "msg": "获取课表成功", "data": result}
            for r in range(0, len(repetIndex), 2):  # 索引数组两两成对，故步进2循环
                fir = repetIndex[r]
                sec = repetIndex[r + 1]
                if (
                        len(
                            re.findall(
                                r"(\d+)", result["normalCourse"][fir]["courseSection"]
                            )
                        )
                        == 4
                ):
                    result["normalCourse"][fir]["courseSection"] = (
                            re.findall(
                                r"(\d+)", result["normalCourse"][fir]["courseSection"]
                            )[0]
                            + "-"
                            + re.findall(
                        r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    )[1]
                            + "节"
                    )
                    result["normalCourse"][fir]["includeSection"] = self.listTime(
                        re.findall(
                            r"(\d+)", result["normalCourse"][fir]["courseSection"]
                        )
                    )
                    # result["normalCourse"][fir]["upTime"] = self.upTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    #     )
                    # )
                    # result["normalCourse"][fir]["courseTime"] = self.calTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    #     )
                    # )

                    result["normalCourse"][sec]["courseSection"] = (
                            re.findall(
                                r"(\d+)", result["normalCourse"][sec]["courseSection"]
                            )[2]
                            + "-"
                            + re.findall(
                        r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    )[3]
                            + "节"
                    )
                    result["normalCourse"][sec]["includeSection"] = self.listTime(
                        re.findall(
                            r"(\d+)", result["normalCourse"][sec]["courseSection"]
                        )
                    )
                    # result["normalCourse"][sec]["upTime"] = self.upTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    #     )
                    # )
                    # result["normalCourse"][sec]["courseTime"] = self.calTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    #     )
                    # )
                else:
                    pass
            return {"code": 1000, "msg": "获取课表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取课表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取课表时未记录的错误：" + traceback.format_exc()}

    def getSchedule(self, year, term):
        """获取课程表信息"""
        url = urljoin(BASE_URL, "/kbcx/xskbcx_cxXsKb.html?gnmkdm=N2151")
        dict = {"1": "3", "2": "12"}
        if dict.get(term) is not None:
            term = dict.get(term)
        else:
            return {"code": 1006, "msg": "错误的学期编号：" + str(term)}
        data = {"xnm": year, "xqm": term}
        try:
            req_schedule = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_schedule.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_schedule.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            schedule = req_schedule.json()
            if len(schedule["kbList"]) == 0 and len(schedule["jxhjkcList"]) == 0 and len(schedule["sjkList"]) == 0:
                return {"code": 1021, "msg": "该学年学期尚无您的课表"}
            if False if schedule.get("xkkg") is None else not schedule["xkkg"]:
                return {"code": 1022, "msg": "该学年学期的课表尚未开放"}
            result = {
                "name": schedule["xsxx"]["XM"],
                "studentId": schedule["xsxx"]["XH"],
                "schoolYear": schedule["xsxx"]["XNM"],
                "schoolTerm": schedule["xsxx"]["XQMMC"],
                "normalCourse": [
                    {
                        "courseTitle": i.get("kcmc"),
                        'courseTitleShort': i.get('kcmc')[0:9] + '..' if len(i.get('kcmc')) > 9 else i.get('kcmc'),
                        "teacher": "无" if i.get("xm") is None else i["xm"],
                        "courseId": i.get("kch_id"),
                        "courseWeekday": i.get("xqj"),
                        "courseSection": i.get("jc"),
                        "courseSectionStart": self.getCourseSectionStart(re.findall(r"(\d+)", i["jc"])),
                        "courseSectionContinue": self.getCourseSectionContinue(re.findall(r"(\d+)", i["jc"])),
                        "includeSection": self.listTime(re.findall(r"(\d+)", i["jc"])),
                        # "upTime": self.upTime(re.findall(r"(\d+)", i["jc"])),
                        # "courseTime": self.calTime(re.findall(r"(\d+)", i["jc"])),
                        "courseWeek": i.get("zcd"),
                        "includeWeeks": self.calWeeks(re.findall(r"[^,]+", i["zcd"])),
                        "exam": i.get("khfsmc"),
                        "campus": i.get("xqmc"),
                        "courseRoom": i.get("cdmc"),
                        "courseRoomShort": self.subCourseRoomStr(str(i.get("cdmc"))),
                        "className": i.get("jxbmc"),
                        "classComposition": i.get("jxbzc"),
                        "hoursComposition": i.get("kcxszc"),
                        "weeklyHours": i.get("zhxs"),
                        "totalHours": i.get("zxs"),
                        "credit": "0.0" if i.get("xf") == "无" else format(float(i.get("xf")), ".1f"),
                    }
                    for i in schedule["kbList"]
                ],
                "otherCourse": [{
                    'courseTitle': i.get('kcmc'),
                    'teacher': i.get('jsxm'),
                    'courseWeek': i.get('qsjsz'),
                    'courseText': i.get('qtkcgs'),
                    'credit': '0.0' if i.get('xf') == '无' else format(float(i.get('xf')), '.1f')
                } for i in schedule['sjkList']]
            }
            """
                处理同周同天同课程不同时段合并显示的问题
            """
            repetIndex = []
            count = 0
            for items in result["normalCourse"]:
                for index in range(len(result["normalCourse"])):
                    if (result["normalCourse"]).index(items) == count:  # 如果对比到自己就忽略
                        pass
                    elif (
                            items["courseTitle"]
                            == result["normalCourse"][index]["courseTitle"]  # 同周同天同课程
                            and items["courseWeekday"]
                            == result["normalCourse"][index]["courseWeekday"]
                            and items["courseWeek"]
                            == result["normalCourse"][index]["courseWeek"]
                    ):
                        repetIndex.append(index)  # 满足条件记录索引
                    else:
                        pass
                count = count + 1  # 记录当前对比课程的索引
            if len(repetIndex) % 2 != 0:  # 暂时考虑一天两个时段上同一门课，不满足条件不进行修改
                return {"code": 1000, "msg": "获取课表成功", "data": result}
            for r in range(0, len(repetIndex), 2):  # 索引数组两两成对，故步进2循环
                fir = repetIndex[r]
                sec = repetIndex[r + 1]
                if (
                        len(
                            re.findall(
                                r"(\d+)", result["normalCourse"][fir]["courseSection"]
                            )
                        )
                        == 4
                ):
                    result["normalCourse"][fir]["courseSection"] = (
                            re.findall(
                                r"(\d+)", result["normalCourse"][fir]["courseSection"]
                            )[0]
                            + "-"
                            + re.findall(
                        r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    )[1]
                            + "节"
                    )
                    result["normalCourse"][fir]["includeSection"] = self.listTime(
                        re.findall(
                            r"(\d+)", result["normalCourse"][fir]["courseSection"]
                        )
                    )
                    # result["normalCourse"][fir]["upTime"] = self.upTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    #     )
                    # )
                    # result["normalCourse"][fir]["courseTime"] = self.calTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    #     )
                    # )

                    result["normalCourse"][sec]["courseSection"] = (
                            re.findall(
                                r"(\d+)", result["normalCourse"][sec]["courseSection"]
                            )[2]
                            + "-"
                            + re.findall(
                        r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    )[3]
                            + "节"
                    )
                    result["normalCourse"][sec]["includeSection"] = self.listTime(
                        re.findall(
                            r"(\d+)", result["normalCourse"][sec]["courseSection"]
                        )
                    )
                    # result["normalCourse"][sec]["upTime"] = self.upTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    #     )
                    # )
                    # result["normalCourse"][sec]["courseTime"] = self.calTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    #     )
                    # )
                else:
                    pass
            return {"code": 1000, "msg": "获取课表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取课表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取课表时未记录的错误：" + traceback.format_exc()}

    def getScheduleByClass(self, year, term, gradeId, majorId, classId):
        """通过班级id获取课程表信息"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/kbdy/bjkbdy_cxBjKb.html?gnmkdm=N214510")
        else:
            url = urljoin(BASE_URL, "/kbdy/bjkbdy_cxBjKb.html?gnmkdm=N214505")
        dict = {"1": "3", "2": "12"}
        if dict.get(term) is not None:
            term = dict.get(term)
        else:
            return {"code": 1006, "msg": "错误的学期编号：" + str(term)}
        data = {
            "xnm": year,
            "xqm": term,
            "njdm_id": gradeId,
            "zyh_id": majorId,
            "bh_id": classId,
            "tjkbzdm": 1,
            "tjkbzxsdm": 0
        }
        try:
            req_schedule = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_schedule.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_schedule.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            schedule = req_schedule.json()
            if len(schedule["kbList"]) == 0 and len(schedule["jxhjkcList"]) == 0 and len(schedule["sjkList"]) == 0:
                return {"code": 1021, "msg": "该学年学期尚无您的课表"}
            # if False if schedule.get("xkkg") is None else not schedule["xkkg"]:
            #     return {"code": 1022, "msg": "该学年学期的课表尚未开放"}
            result = {
                "normalCourse": [
                    {
                        "courseTitle": i.get("kcmc"),
                        'courseTitleShort': i.get('kcmc')[0:9] + '..' if len(i.get('kcmc')) > 9 else i.get('kcmc'),
                        "teacher": "无" if i.get("xm") is None else i["xm"],
                        "courseId": "无" if i.get("kch_id") is None else i["kch_id"],
                        "courseWeekday": i.get("xqj"),
                        "courseSection": i.get("jc"),
                        "courseSectionStart": self.getCourseSectionStart(re.findall(r"(\d+)", i["jc"])),
                        "courseSectionContinue": self.getCourseSectionContinue(re.findall(r"(\d+)", i["jc"])),
                        "includeSection": self.listTime(re.findall(r"(\d+)", i["jc"])),
                        # "upTime": self.upTime(re.findall(r"(\d+)", i["jc"])),
                        # "courseTime": self.calTime(re.findall(r"(\d+)", i["jc"])),
                        "courseWeek": i.get("zcd"),
                        "includeWeeks": self.calWeeks(re.findall(r"[^,]+", i["zcd"])),
                        "exam": i.get("khfsmc"),
                        "campus": i.get("xqmc"),
                        "courseRoom": i.get("cdmc"),
                        "courseRoomShort": self.subCourseRoomStr(str(i.get("cdmc"))),
                        "className": i.get("jxbmc"),
                        "hoursComposition": i.get("kcxszc"),
                        "weeklyHours": i.get("zhxs"),
                        "totalHours": i.get("zxs"),
                    }
                    for i in schedule["kbList"]
                ],
                "otherCourse": [{
                    'courseTitle': i.get('kcmc'),
                    'teacher': i.get('jsxm'),
                    'courseWeek': i.get('qsjsz'),
                    'courseText': i.get('qtkcgs'),
                } for i in schedule['sjkList']]
            }
            """
                处理同周同天同课程不同时段合并显示的问题
            """
            repetIndex = []
            count = 0
            for items in result["normalCourse"]:
                for index in range(len(result["normalCourse"])):
                    if (result["normalCourse"]).index(items) == count:  # 如果对比到自己就忽略
                        pass
                    elif (
                            items["courseTitle"]
                            == result["normalCourse"][index]["courseTitle"]  # 同周同天同课程
                            and items["courseWeekday"]
                            == result["normalCourse"][index]["courseWeekday"]
                            and items["courseWeek"]
                            == result["normalCourse"][index]["courseWeek"]
                    ):
                        repetIndex.append(index)  # 满足条件记录索引
                    else:
                        pass
                count = count + 1  # 记录当前对比课程的索引
            if len(repetIndex) % 2 != 0:  # 暂时考虑一天两个时段上同一门课，不满足条件不进行修改
                return {"code": 1000, "msg": "获取课表成功", "data": result}
            for r in range(0, len(repetIndex), 2):  # 索引数组两两成对，故步进2循环
                fir = repetIndex[r]
                sec = repetIndex[r + 1]
                if (
                        len(
                            re.findall(
                                r"(\d+)", result["normalCourse"][fir]["courseSection"]
                            )
                        )
                        == 4
                ):
                    result["normalCourse"][fir]["courseSection"] = (
                            re.findall(
                                r"(\d+)", result["normalCourse"][fir]["courseSection"]
                            )[0]
                            + "-"
                            + re.findall(
                        r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    )[1]
                            + "节"
                    )
                    result["normalCourse"][fir]["includeSection"] = self.listTime(
                        re.findall(
                            r"(\d+)", result["normalCourse"][fir]["courseSection"]
                        )
                    )
                    # result["normalCourse"][fir]["upTime"] = self.upTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    #     )
                    # )
                    # result["normalCourse"][fir]["courseTime"] = self.calTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][fir]["courseSection"]
                    #     )
                    # )

                    result["normalCourse"][sec]["courseSection"] = (
                            re.findall(
                                r"(\d+)", result["normalCourse"][sec]["courseSection"]
                            )[2]
                            + "-"
                            + re.findall(
                        r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    )[3]
                            + "节"
                    )
                    result["normalCourse"][sec]["includeSection"] = self.listTime(
                        re.findall(
                            r"(\d+)", result["normalCourse"][sec]["courseSection"]
                        )
                    )
                    # result["normalCourse"][sec]["upTime"] = self.upTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    #     )
                    # )
                    # result["normalCourse"][sec]["courseTime"] = self.calTime(
                    #     re.findall(
                    #         r"(\d+)", result["normalCourse"][sec]["courseSection"]
                    #     )
                    # )
                else:
                    pass
            return {"code": 1000, "msg": "获取课表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取课表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取课表时未记录的错误：" + traceback.format_exc()}

    def getSchedulePDF(self, name, year, term):
        """获取课表pdf"""
        url_policy = urljoin(BASE_URL, "/kbdy/bjkbdy_cxXnxqsfkz.html")
        url_file = urljoin(BASE_URL, "/kbcx/xskbcx_cxXsShcPdf.html")
        origin_term = term
        dict = {"1": "3", "2": "12", "0": ""}  # 修改检测学期
        if dict.get(term) is not None:
            term = dict.get(term)
        else:
            return {"code": 1006, "msg": "错误的学期编号：" + str(term)}
        data = {
            "xnm": year,
            "xqm": term,
            "xnmc": year + "-" + str(int(year) + 1),
            "xqmmc": origin_term,
            "jgmc": "undefined",
            "xm": name,
            "xxdm": "",
            "xszd.sj": "true",
            "xszd.cd": "true",
            "xszd.js": "true",
            "xszd.jszc": "false",
            "xszd.jxb": "true",
            "xszd.xkbz": "true",
            "xszd.kcxszc": "true",
            "xszd.zhxs": "true",
            "xszd.zxs": "true",
            "xszd.khfs": "true",
            "xszd.xf": "true",
            "xszd.skfsmc": "false",
            "kzlx": "dy"
        }

        try:
            # 许可接口
            pilicy_params = {
                "gnmkdm": "N2151"
            }
            req_policy = self.sess.post(
                url_policy,
                headers=self.headers,
                data=data,
                params=pilicy_params,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_policy.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_policy.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            # 获取PDF文件URL
            file_params = {"doType": "table"}
            req_file = self.sess.post(
                url_file,
                headers=self.headers,
                data=data,
                params=file_params,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            doc = pq(req_file.text)
            if doc("title").text() == "错误提示":
                error = doc("p.error_title").text()
                return {"code": 999, "msg": "错误：" + error}
            result = req_file.content  # 二进制内容
            return {"code": 1000, "msg": "获取课程表pdf成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取课程表pdf超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取课程表pdf时未记录的错误：" + traceback.format_exc()}

    def getStudy(self, sid):
        """获取学业情况"""
        url_main = urljoin(
            BASE_URL, "/xsxy/xsxyqk_cxXsxyqkIndex.html?gnmkdm=N105515&layout=default",
        )
        url_info = urljoin(
            BASE_URL, "/xsxy/xsxyqk_cxJxzxjhxfyqKcxx.html?gnmkdm=N105515"
        )
        try:
            req_main = self.sess.get(
                url_main,
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT,
                stream=True,
            )
            if self.login_url_nodomain in req_main.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc_main = pq(req_main.text)
            # if doc_main("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            allc_str = [allc.text() for allc in doc_main("font[size='2px']").items()]
            gpa = float(allc_str[2])
            allc_num = re.findall(r"\d+", allc_str[3])
            allc_num2 = re.findall(r"\d+", allc_str[5])
            allc_num.append(allc_num2[0])
            ipa = int(allc_num[0])
            ipp = int(allc_num[1])
            ipf = int(allc_num[2])
            ipn = int(allc_num[3])
            ipi = int(allc_num[4])
            allc_num3 = re.findall(r"\d+", allc_str[6])
            allc_num4 = re.findall(r"\d+", allc_str[7])
            opp = int(allc_num3[0])
            opf = int(allc_num4[0])

            id_find = re.findall(r"xfyqjd_id='(.*)' jdkcsx='1' leaf=''", req_main.text)
            id_find2 = re.findall(r"xfyqjd_id='(.*)' jdkcsx='2' leaf=''", req_main.text)
            idList = list({}.fromkeys(id_find).keys())
            idList2 = list({}.fromkeys(id_find2).keys())
            tsid = "None"
            tzid = "None"
            zyid = "None"
            qtid = "None"
            # 本校特色，不同年级获取四项id的方法不同
            if int(sid[0:4]) < 2019:
                for i in idList:
                    if re.findall(r"tsjy", i):
                        tsid = i[0:14]
                    elif re.findall(r"tzjy", i):
                        tzid = i[0:14]
                    elif re.findall(r"zyjy", i):
                        zyid = i[0:14]
                    elif re.findall(r"qtkcxfyq", i):
                        qtid = i
            elif int(sid[0:4]) == 2019:
                tsid = idList[0]
                tzid = idList[2]
                zyid = idList[1]
                qtid = idList2[0]
            elif int(sid[0:4]) >= 2020:
                tsid = idList[0]
                tzid = idList[2]
                zyid = idList[1]
                qtid = idList[3]
            else:
                tsid = idList[0]
                tzid = idList[2]
                zyid = idList[1]
                qtid = idList2[0]

            req_ts = self.sess.post(
                url_info,
                headers=self.headers,
                data={"xfyqjd_id": tsid},
                cookies=self.cookies,
                timeout=TIMEOUT,
                stream=True,
            )
            req_tz = self.sess.post(
                url_info,
                headers=self.headers,
                data={"xfyqjd_id": tzid},
                cookies=self.cookies,
                timeout=TIMEOUT,
                stream=True,
            )
            req_zy = self.sess.post(
                url_info,
                headers=self.headers,
                data={"xfyqjd_id": zyid},
                cookies=self.cookies,
                timeout=TIMEOUT,
                stream=True,
            )
            req_qt = self.sess.post(
                url_info,
                headers=self.headers,
                data={"xfyqjd_id": qtid},
                cookies=self.cookies,
                timeout=TIMEOUT,
                stream=True,
            )
            ts_point_find = re.findall(
                r"通识(.*)&nbsp;要求学分:(\d+\.\d+)&nbsp;获得学分:(\d+\.\d+)&nbsp;&nbsp;未获得学分:(\d+\.\d+)&nbsp",
                req_main.text,
            )
            ts_point_list = list(
                list({}.fromkeys(ts_point_find).keys())[0]
            )  # 先得到元组再拆开转换成列表
            ts_point = {
                "tsr": ts_point_list[1],
                "tsg": ts_point_list[2],
                "tsn": ts_point_list[3],
            }
            tz_point_find = re.findall(
                r"拓展(.*)&nbsp;要求学分:(\d+\.\d+)&nbsp;获得学分:(\d+\.\d+)&nbsp;&nbsp;未获得学分:(\d+\.\d+)&nbsp",
                req_main.text,
            )
            tz_point_list = list(list({}.fromkeys(tz_point_find).keys())[0])
            tz_point = {
                "tzr": tz_point_list[1],
                "tzg": tz_point_list[2],
                "tzn": tz_point_list[3],
            }
            zy_point_find = re.findall(
                r"专业(.*)&nbsp;要求学分:(\d+\.\d+)&nbsp;获得学分:(\d+\.\d+)&nbsp;&nbsp;未获得学分:(\d+\.\d+)&nbsp",
                req_main.text,
            )
            zy_point_list = list(list({}.fromkeys(zy_point_find).keys())[0])
            zy_point = {
                "zyr": zy_point_list[1],
                "zyg": zy_point_list[2],
                "zyn": zy_point_list[3],
            }
            result = {
                "gpa": str(gpa)
                if gpa != "" and gpa is not None
                else "init",  # 平均学分绩点GPA
                "ipa": ipa,  # 计划内总课程数
                "ipp": ipp,  # 计划内已过课程数
                "ipf": ipf,  # 计划内未过课程数
                "ipn": ipn,  # 计划内未修课程数
                "ipi": ipi,  # 计划内在读课程数
                "opp": opp,  # 计划外已过课程数
                "opf": opf,  # 计划外未过课程数
                "tsData": {
                    "tsPoint": ts_point,  # 通识教育学分情况
                    "tsItems": [
                        {
                            "courseTitle": j.get("KCMC"),
                            "courseId": j.get("KCH"),
                            "courseSituation": j.get("XDZT"),
                            "courseTerm": self.formatTermCN(
                                sid, j.get("JYXDXNM"), j.get("JYXDXQMC")
                            ),
                            "courseCategory": "无"
                            if j.get("KCLBMC") is None
                            else j["KCLBMC"],
                            "courseAttribution": "无"
                            if j.get("KCXZMC") is None
                            else j["KCXZMC"],
                            "maxGrade": " " if j.get("MAXCJ") is None else j["MAXCJ"],
                            "credit": " "
                            if j.get("XF") is None
                            else format(float(j["XF"]), ".1f"),
                            "gradePoint": " "
                            if j.get("JD") is None
                            else format(float(j["JD"]), ".1f"),
                        }
                        for j in req_ts.json()
                    ],  # 通识教育修读情况
                },
                "tzData": {
                    "tzPoint": tz_point,  # 拓展教育学分情况
                    "tzItems": [
                        {
                            "courseTitle": k.get("KCMC"),
                            "courseId": k.get("KCH"),
                            "courseSituation": k.get("XDZT"),
                            "courseTerm": self.formatTermCN(
                                sid, k.get("JYXDXNM"), k.get("JYXDXQMC")
                            ),
                            "courseCategory": "无"
                            if k.get("KCLBMC") is None
                            else k["KCLBMC"],
                            "courseAttribution": "无"
                            if k.get("KCXZMC") is None
                            else k["KCXZMC"],
                            "maxGrade": " " if k.get("MAXCJ") is None else k["MAXCJ"],
                            "credit": " "
                            if k.get("XF") is None
                            else format(float(k["XF"]), ".1f"),
                            "gradePoint": " "
                            if k.get("JD") is None
                            else format(float(k["JD"]), ".1f"),
                        }
                        for k in req_tz.json()
                    ],  # 拓展教育修读情况
                },
                "zyData": {
                    "zyPoint": zy_point,  # 专业教育学分情况
                    "zyItems": [
                        {
                            "courseTitle": l.get("KCMC"),
                            "courseId": l.get("KCH"),
                            "courseSituation": l.get("XDZT"),
                            "courseTerm": self.formatTermCN(
                                sid, l.get("JYXDXNM"), l.get("JYXDXQMC")
                            ),
                            "courseCategory": "无"
                            if l.get("KCLBMC") is None
                            else l["KCLBMC"],
                            "courseAttribution": "无"
                            if l.get("KCXZMC") is None
                            else l["KCXZMC"],
                            "maxGrade": " " if l.get("MAXCJ") is None else l["MAXCJ"],
                            "credit": " "
                            if l.get("XF") is None
                            else format(float(l["XF"]), ".1f"),
                            "gradePoint": " "
                            if l.get("JD") is None
                            else format(float(l["JD"]), ".1f"),
                        }
                        for l in req_zy.json()
                    ],  # 专业教育修读情况
                },
                "qtData": {
                    "qtPoint": "{}",  # 其它课程学分情况
                    "qtItems": [
                        {
                            "courseTitle": m.get("KCMC"),
                            "courseId": m.get("KCH"),
                            "courseSituation": m.get("XDZT"),
                            "courseTerm": self.formatTermCN(sid, m["XNM"], m["XQMMC"]),
                            "courseCategory": self.catByCourseId(m.get("KCH")),
                            "courseAttribution": " "
                            if m.get("KCXZMC") is None
                            else m["KCXZMC"],
                            "maxGrade": " " if m.get("MAXCJ") is None else m["MAXCJ"],
                            "credit": " "
                            if m.get("XF") is None
                            else format(float(m["XF"]), ".1f"),
                            "gradePoint": " "
                            if m.get("JD") is None
                            else format(float(m["JD"]), ".1f"),
                        }
                        for m in req_qt.json()
                    ],  # 其它课程修读情况
                },
            }
            return {"code": 1000, "msg": "获取学业情况成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取学业情况超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取学业情况时未记录的错误：" + traceback.format_exc()}

    def getGradePDF(self, sid):
        """获取学生成绩总表pdf"""
        url_view = urljoin(BASE_URL, "/bysxxcx/xscjzbdy_dyXscjzbView.html")
        url_window = urljoin(BASE_URL, "/bysxxcx/xscjzbdy_dyCjdyszxView.html")
        url_policy = urljoin(BASE_URL, "/xtgl/bysxxcx/xscjzbdy_cxXsCount.html")
        url_filetype = urljoin(BASE_URL, "/bysxxcx/xscjzbdy_cxGswjlx.html")
        url_common = urljoin(BASE_URL, "/common/common_cxJwxtxx.html")
        url_file = urljoin(BASE_URL, "/bysxxcx/xscjzbdy_dyList.html")
        url_progress = urljoin(BASE_URL, "/xtgl/progress_cxProgressStatus.html")
        data = {
            "gsdygx": "10628-zw-mrgs",
            "ids": "",
            "bdykcxzDms": "",
            "cytjkcxzDms": "",
            "cytjkclbDms": "",
            "cytjkcgsDms": "",
            "bjgbdykcxzDms": "",
            "bjgbdyxxkcxzDms": "",
            "djksxmDms": "",
            "cjbzmcDms": "",
            "cjdySzxs": "",
            "wjlx": "pdf",
        }

        try:
            data_view = {
                "time": str(round(time.time() * 1000)),
                "gnmkdm": "N558020",
                "su": str(sid),
            }
            data_params = data_view
            del data_params["time"]
            # View接口
            req_view = self.sess.post(
                url_view,
                headers=self.headers,
                data=data_view,
                params=data_view,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_view.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_view.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            # Window接口
            data_window = {"xh": ""}
            self.sess.post(
                url_window,
                headers=self.headers,
                data=data_window,
                params=data_params,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            # 许可接口
            data_policy = data
            del data_policy["wjlx"]
            self.sess.post(
                url_policy,
                headers=self.headers,
                data=data_policy,
                params=data_params,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            # 文件类型接口
            data_filetype = data_policy
            self.sess.post(
                url_filetype,
                headers=self.headers,
                data=data_filetype,
                params=data_params,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            # Common接口
            self.sess.post(
                url_common,
                headers=self.headers,
                data=data_params,
                params=data_params,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            # 获取PDF文件URL
            req_file = self.sess.post(
                url_file,
                headers=self.headers,
                data=data,
                params=data_params,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            doc = pq(req_file.text)
            if doc("title").text() == "错误提示":
                error = doc("p.error_title").text()
                return {"code": 999, "msg": "错误：" + error}
            # 进度接口
            data_progress = {
                "key": "score_print_processed",
                "gnmkdm": "N558020",
                "su": str(sid),
            }
            self.sess.post(
                url_progress,
                headers=self.headers,
                data=data_progress,
                params=data_progress,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            # 生成PDF文件URL
            pdf = (
                req_file.text.replace("#成功", "")
                .replace('"', "")
                .replace("/", "\\")
                .replace("\\\\", "/")
            )
            # 下载PDF文件
            req_pdf = self.sess.get(
                urljoin(BASE_URL, pdf),
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT + 2,
            )
            result = req_pdf.content  # 二进制内容
            return {"code": 1000, "msg": "获取学生成绩总表pdf成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取成绩总表pdf超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取成绩总表pdf时未记录的错误：" + traceback.format_exc()}

    def getMessage(self):
        """获取消息"""

        def makeLineFeed(str):
            if str is not None:
                return str[:str.find(":")] + ":\\n" + str[str.find(":") + 1:]
            else:
                return None

        url = urljoin(BASE_URL, "/xtgl/index_cxDbsy.html?doType=query")
        data = {
            "sfyy": "0",  # 是否已阅，未阅未1，已阅为2
            "flag": "1",
            "_search": "false",
            "nd": int(time.time() * 1000),
            "queryModel.showCount": "1000",  # 最多条数
            "queryModel.currentPage": "1",  # 当前页数
            "queryModel.sortName": "cjsj",
            "queryModel.sortOrder": "desc",  # 时间倒序, asc正序
            "time": "0",
        }
        try:
            req_msg = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            # if self.login_url_nodomain in req_msg.url:
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(req_msg.text)
            if doc("h5").text() == "用户登录" or doc("title").text() == "错误提示":
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            msg = req_msg.json()
            result = [
                {"message": makeLineFeed(i.get("xxnr")), "ctime": i.get("cjsj")}
                for i in msg.get("items")
            ]
            return {"code": 1000, "msg": "获取消息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取消息超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取消息时未记录的错误：" + traceback.format_exc()}

    def getNowClass(self):
        """获取当前班级"""
        url = urljoin(BASE_URL, "/xsxxxggl/xsxxwh_cxCkDgxsxx.html?gnmkdm=N100801")
        try:
            req_class = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_class.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_class.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            info = req_class.json()
            result = info.get("xjztdm") if info.get("bh_id") is None else info["bh_id"]
            return {"code": 1000, "msg": "获取当前班级成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取当前班级超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取当前班级时未记录的错误：" + traceback.format_exc()}

    def getGPA(self):
        """获取GPA"""
        url = urljoin(
            BASE_URL, "/xsxy/xsxyqk_cxXsxyqkIndex.html?gnmkdm=N105515&layout=default",
        )
        req_gpa = self.sess.get(
            url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
        )
        if self.login_url_nodomain in req_gpa.url:
            return {"code": 1013, "msg": "登录过期，请重新登录"}
        doc = pq(req_gpa.text)
        # if doc("h5").text() == "用户登录":
        #     return {"code": 1013, "msg": "登录过期，请重新登录"}
        allc_str = [allc.text() for allc in doc("font[size='2px']").items()]
        try:
            gpa = float(allc_str[2])
            if gpa != "" and gpa is not None:
                return gpa
            else:
                return "init"
        except Exception as e:
            # if "list index" in traceback.format_exc():
            #     return "init"
            return "init"

    def catByCourseId(self, course_id):
        """根据课程号获取类别"""
        url = urljoin(BASE_URL, "/jxjhgl/common_cxKcJbxx.html?id=" + course_id)
        req_category = self.sess.get(
            url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
        )
        doc = pq(req_category.text)
        th_list = doc("th")
        try:
            data_list = [
                (content.text).strip()
                for content in th_list
                if (content.text).strip() != ""
            ]
            return data_list[5]
        except:
            return "未知类别"

    def getCollegesList(self):
        """获取所有学院"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/kbdy/bjkbdy_cxBjkbdyIndex.html?gnmkdm=N214510")
        else:
            url = urljoin(BASE_URL, "/kbdy/bjkbdy_cxBjkbdyIndex.html?gnmkdm=N214505")
        try:
            req_all_colleges = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_all_colleges.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(req_all_colleges.text, parser="html")
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            result = []
            for option_item in doc.find('select#jg_id option').items():
                colleges_item = {
                    'name': pq(option_item).text(),
                    'value': pq(option_item).attr('value')
                }
                result.append(colleges_item)
            return {"code": 1000, "msg": "获取学院列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取学院列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取学院列表时未记录的错误：" + traceback.format_exc()}

    def getCollegeGradeList(self):
        """获取所有年级列表"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/kbdy/bjkbdy_cxBjkbdyIndex.html?gnmkdm=N214510")
        else:
            url = urljoin(BASE_URL, "/kbdy/bjkbdy_cxBjkbdyIndex.html?gnmkdm=N214505")
        try:
            req_all_colleges = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_all_colleges.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(req_all_colleges.text, parser="html")
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            result = []
            for option_item in doc.find('select#njdm_id option').items():
                colleges_item = {
                    'name': pq(option_item).text(),
                    'value': pq(option_item).attr('value')
                }
                result.append(colleges_item)
            return {"code": 1000, "msg": "获取所有年级列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取所有年级列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取所有年级列表时未记录的错误：" + traceback.format_exc()}

    def getMajorList(self, college_id, grade_id="0000"):
        """根据学院获取专业"""
        if self.is_teacher:
            url = urljoin(
                BASE_URL,
                "/xtgl/comm_cxZydmList.html?jg_id=" + college_id + "&njdm_id=" + grade_id + "&gnmkdm=N214510"
            )
        else:
            url = urljoin(
                BASE_URL,
                "/xtgl/comm_cxZydmList.html?jg_id=" + college_id + "&njdm_id=" + grade_id + "&gnmkdm=N214505"
            )
        try:
            req_major = self.sess.get(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_major.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_major.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            major_list = req_major.json()
            result = [
                {
                    "majorNumber": i.get("zyh"),
                    'majorId': i.get('zyh_id'),
                    "majorName": i.get('zymc')
                } for i in major_list
            ]
            return {"code": 1000, "msg": "获取专业列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取专业列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取专业列表时未记录的错误：" + traceback.format_exc()}

    def getClassList1(self, college_id, grade_id):
        """根据学院，年级获取班级"""
        if self.is_teacher:
            url = urljoin(
                BASE_URL,
                "/xtgl/comm_cxBjdmList.html?jg_id=" + college_id + "&njdm_id=" + grade_id + "&gnmkdm=N214510"
            )
        else:
            url = urljoin(
                BASE_URL,
                "/xtgl/comm_cxBjdmList.html?jg_id=" + college_id + "&njdm_id=" + grade_id + "&gnmkdm=N214505"
            )
        try:
            req_major = self.sess.get(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_major.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_major.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            major_list = req_major.json()
            result = [
                {
                    "classNumber": i.get("bh"),
                    'classId': i.get('bh_id'),
                    "className": i.get('bj'),
                    "gradeId": i.get('njdm_id'),
                    "majorNumber": i.get('zyh'),
                    "majorId": i.get('zyh_id'),
                    "najorName": i.get('zymc')
                } for i in major_list
            ]
            return {"code": 1000, "msg": "获取班级列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取班级列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取班级列表时未记录的错误：" + traceback.format_exc()}

    def getClassList2(self, year, term, college_id, grade_id, major_id=""):
        """根据学院，年级获取班级"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/kbdy/bjkbdy_cxBjkbdyTjkbList.html?gnmkdm=N214510")
        else:
            url = urljoin(BASE_URL, "/kbdy/bjkbdy_cxBjkbdyTjkbList.html?gnmkdm=N214505")
        dict = {"1": "3", "2": "12", "0": ""}  # 修改检测学期
        if dict.get(term) is not None:
            term1 = dict.get(term)
        else:
            return {"code": 1006, "msg": "错误的学期编号：" + str(term)}
        try:
            data = {
                "xnm": year,  # 学年名:2021
                "xqm": term1,  # 学期名:3,12
                "xqh_id": "",
                "njdm_id": grade_id,  # 年级：2020
                "jg_id": college_id,  # 学院id：01
                "zyh_id": major_id,
                "_search": False,
                "queryModel.showCount": "2000",  # 最多条数
                "queryModel.currentPage": "1",  # 当前页数
                "queryModel.sortName": "",
                "queryModel.sortOrder": "asc",  # 时间倒序, asc正序
                "time": "0",
            }
            req_class = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_class.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            # doc = pq(req_class.text)
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            class_list = req_class.json()
            result = [
                {
                    'classId': i.get('bh_id'),
                    "className": i.get('bj'),
                    "gradeId": i.get('njdm_id'),
                    "gradeNumber": i.get('njmc'),
                    "yearId": i.get('xnm'),
                    "yearName": i.get('xnmc'),
                    "termId": i.get('xqh_id'),
                    "termName": i.get('xqm'),
                    "campus": i.get('xqmc'),
                    "majorId": i.get('zyh_id'),
                    "majorName": i.get('zymc')
                } for i in class_list["items"]
            ]
            return {"code": 1000, "msg": "获取班级列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取班级列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": "获取班级列表时未记录的错误：" + traceback.format_exc()}

    def getTeachingPlanGradeList(self):
        """教学计划-获取所有年级列表"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html?gnmkdm=N156025")
        else:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html?gnmkdm=N153540")
        try:
            req_grade = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_grade.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(req_grade.text, parser="html")
            result = []
            for option_item in doc.find('select#nj_cx option').items():
                colleges_item = {
                    'name': pq(option_item).text(),
                    'value': pq(option_item).attr('value')
                }
                result.append(colleges_item)
            return {"code": 1000, "msg": "获取所有教学计划年级列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取教学计划年级列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取教学计划年级列表时未记录的错误：" + traceback.format_exc()}

    def getTeachingPlanCollegesList(self):
        """教学计划-获取所有学院列表"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html?gnmkdm=N156025")
        else:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html?gnmkdm=N153540")
        try:
            req_all_colleges = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_all_colleges.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            doc = pq(req_all_colleges.text, parser="html")
            # if doc("h5").text() == "用户登录":
            #     return {"code": 1013, "msg": "登录过期，请重新登录"}
            result = []
            for option_item in doc.find('select#jg_id option').items():
                colleges_item = {
                    'name': pq(option_item).text(),
                    'value': pq(option_item).attr('value')
                }
                result.append(colleges_item)
            return {"code": 1000, "msg": "获取教学计划学院列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取教学计划学院列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取教学计划学院列表时未记录的错误：" + traceback.format_exc()}

    def getTeachingPlanMajorList(self, grade_id, college_id=''):
        """教学计划-获取专业列表"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html?doType=query&gnmkdm=N156025")
        else:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html?doType=query&gnmkdm=N153540")
        data = {
            "jg_id": college_id,  # 学院id
            "njdm_id": grade_id,  # 年级id
            "dlbs": '',
            "zyh_id": '',
            "currentPage_cx": '',
            "_search": False,
            "nd": int(time.time() * 1000),
            "queryModel.showCount": "1000",  # 最多条数
            "queryModel.currentPage": "1",  # 当前页数
            "queryModel.sortName": "",
            "queryModel.sortOrder": "asc",  # 时间倒序, asc正序
            "time": "0",
        }
        try:
            req_major = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_major.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            major = req_major.json()
            result = [
                {
                    "infoId": i.get("jxzxjhxx_id"),  # 教学执行计划信息id
                    "classMark": i.get("dlbs"),  # 大类标记
                    "courseCount": i.get("kcs"),  # 课程数
                    "numberOfStudent": i.get("jhrs"),  # 计划人数
                    "classNumber": i.get("bjgs"),  # 班级个数
                    "majorDirectionNumber": i.get("zyfxgs"),  # 专业方向个数
                    "gradeId": i.get("njdm"),  # 年级id
                    "taskMark": i.get("rwbj"),  # 任务标记
                    "campusId": i.get("xqh_id"),  # 校区id
                    "campusName": i.get("xqmc"),  # 校区名字
                    "schooling": i.get("xz"),  # 学制
                    "majorNumber": i.get("zyh"),  # 专业号
                    "majorName": i.get("zymc"),  # 专业名称
                } for i in major["items"]
            ]
            return {"code": 1000, "msg": "获取教学计划专业列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取教学计划专业列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取教学计划专业列表时未记录的错误：" + traceback.format_exc()}

    def getTeachingPlanMajorDirectionList(self, info_id):
        """教学计划-获取专业方向列表"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhxxwh_cxZyfxxx.html?gnmkdm=N156025&jxzxjhxx_id=" + info_id)
        else:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhxxwh_cxZyfxxx.html?gnmkdm=N153540&jxzxjhxx_id=" + info_id)
        try:
            req_major_direction = self.sess.post(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_major_direction.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            major_direction = req_major_direction.json()
            result = [
                {
                    "majorDirectionNumber": i.get("zyfxdm"),  # 专业方向代码
                    "majorDirectionName": i.get("zyfxmc"),  # 专业方向名称
                    "majorNumber": i.get("zyh"),  # 班级号
                    "majorName": i.get("zymc")  # 专业名
                } for i in major_direction
            ]
            return {"code": 1000, "msg": "获取教学计划专业方向列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取教学计划专业方向列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取教学计划专业方向列表时未记录的错误：" + traceback.format_exc()}

    def getTeachingPlanMajorClassList(self, info_id):
        """教学计划-获取专业班级列表"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhxxwh_cxBjxx.html?gnmkdm=N156025&jxzxjhxx_id=" + info_id)
        else:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhxxwh_cxBjxx.html?gnmkdm=N153540&jxzxjhxx_id=" + info_id)
        try:
            req_major_class = self.sess.post(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_major_class.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            major_class = req_major_class.json()
            result = [
                {
                    "classCode": i.get("bh"),  # 班级代码
                    "classId": i.get("bh_id"),  # 班级Id
                    "className": i.get("bjmc"),  # 班级名称
                    "classSize": i.get("bjrs"),  # 班级人数
                    "majorNumber": i.get("zyh"),  # 专业号
                    "majorName": i.get("zymc"),  # 专业名称
                } for i in major_class
            ]
            return {"code": 1000, "msg": "获取教学计划专业班级列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取教学计划专业班级列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取教学计划专业班级列表时未记录的错误：" + traceback.format_exc()}

    def getTeachingPlanMajorCourseInfoList(self, info_id, suggest_year='', suggest_term='', allow_year='',
                                           allow_term=''):
        """教学计划-获取专业课程信息列表"""
        if self.is_teacher:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhkcxx_cxJxzxjhkcxxIndex.html?doType=query&gnmkdm=N156025")
        else:
            url = urljoin(BASE_URL, "/jxzxjhgl/jxzxjhkcxx_cxJxzxjhkcxxIndex.html?doType=query&gnmkdm=N153540")
        data = {
            "jyxdxnm": suggest_year,
            "jyxdxqm": suggest_term,
            "yxxdxnm": allow_year,
            "yxxdxqm": allow_term,
            "shzt": '',
            "kch": '',
            "jxzxjhxx_id": info_id,
            "xdlx": '',
            "_search": False,
            "nd": int(time.time() * 1000),
            "queryModel.showCount": "1000",  # 最多条数
            "queryModel.currentPage": "1",  # 当前页数
            "queryModel.sortName": "jyxdxnm,jyxdxqm,kch",
            "queryModel.sortOrder": "asc",  # 时间倒序, asc正序
            "time": "0",
        }
        try:
            req_major = self.sess.post(
                url,
                headers=self.headers,
                data=data,
                cookies=self.cookies,
                timeout=TIMEOUT,
            )
            if self.login_url_nodomain in req_major.url:
                return {"code": 1013, "msg": "登录过期，请重新登录"}
            major = req_major.json()
            result = [
                {
                    "courseId": i.get("kch_id"),  # 课程号
                    "courseName": i.get("kcmc"),  # 课程名称
                    "campusName": i.get("xqmc"),  # 校区
                    "credit": i.get("xf"),  # 学分
                    "totalHours": i.get("zxs"),  # 总学时
                    "courseDepartment": i.get("kkbmmc"),  # 开课部门
                    "majorDirection": "无" if i.get("zyfxmc") is None else i.get("zyfxmc"),  # 专业方向
                    "courseCategory": "无" if i.get("kclbmc") is None else i.get("kclbmc"),  # 课程类别
                    "courseType": "无" if i.get("kclxmc") is None else i.get("kclxmc"),  # 课程类型
                    "courseNature": "无" if i.get("kcxzmc") is None else i.get("kcxzmc"),  # 课程性质
                    "mainMark": i.get("zxbj"),  # 主修标记
                    "minorMark": i.get("fxbj"),  # 辅修标记
                    "secondMajorMark": i.get("ezybj"),  # 二专业标记
                    "secondDegreeMark": i.get("exwbj"),  # 二学位标记
                    "majorCoreCourseMark": i.get("zyhxkcbj"),  # 专业核心课程标记
                    "majorOpenCourseMark": i.get("zykfkcbj"),  # 专业开放课程标记
                    "suggestSchoolYear": i.get("jyxdxnm"),  # 建议修读学年
                    "suggestSchoolTerm": i.get("jyxdxqm"),  # 建议修读学期
                    "allowedAcademicYearTerm": i.get("yyxdxnxqmc"),  # 允许修读学年学期
                    "assessmentMethod": "无" if i.get("khfsdm") is None else i.get("khfsdm"),  # 考核方式
                    "examMethod": "无" if i.get("ksfsdm") is None else i.get("ksfsdm"),  # 考试方式
                    "examForm": "无" if i.get("ksxsdm") is None else i.get("ksxsdm")  # 考试形式
                } for i in major["items"]
            ]
            return {"code": 1000, "msg": "获取教学计划课程信息列表成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取教学计划课程信息列表超时"}
        except exceptions.RequestException:
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试或教务系统维护中"}
        except Exception as e:
            if traceback.format_exc() == "'NoneType' object has no attribute 'get'":
                return {"code": 2333, "msg": "请重试或教务系统维护中"}
            traceback.print_exc()
            return {"code": 999, "msg": "获取教学计划课程信息列表时未记录的错误：" + traceback.format_exc()}

    @staticmethod
    def calPoint(grade):
        """计算绩点"""
        if grade is None:
            return "null"
        else:
            if grade.isdigit() is False:
                return "null"
            else:
                return format(float((int(grade) - 60) // 5 * 0.5 + 1), ".1f")

    @staticmethod
    def listTime(args):
        """返回该课程为第几节到第几节"""
        return [n for n in range(int(args[0]), int(args[1]) + 1)]

    @staticmethod
    def getCourseSectionStart(args):
        """返回该课程为第几节到第几节"""
        return int(args[0])

    @staticmethod
    def getCourseSectionContinue(args):
        """返回该课程为第几节到第几节"""
        return int(args[1]) - int(args[0]) + 1

    @staticmethod
    def subCourseRoomStr(str):
        """获取课程地点短名称"""
        return str.replace("教学楼", '')

    @staticmethod
    def formatTermCN(sid, year, term):
        """计算培养方案具体学期转化成中文"""
        grade = int(sid[0:4])
        year = int(year)
        term = int(term)
        dict = {
            grade: "大一上" if term == 1 else "大一下",
            grade + 1: "大二上" if term == 1 else "大二下",
            grade + 2: "大三上" if term == 1 else "大三下",
            grade + 3: "大四上" if term == 1 else "大四下",
        }
        return dict.get(year) if dict.get(year) is not None else "未知"

    @staticmethod
    def calWeeks(args):
        """返回课程所含周列表"""
        week_list = []
        for item in args:
            if "-" in item:
                weeks_pair = re.findall(r"(\d+)", item)
                if len(weeks_pair) != 2:
                    continue
                if "单" in item:
                    for i in range(int(weeks_pair[0]), int(weeks_pair[1]) + 1):
                        if i % 2 == 1:
                            week_list.append(i)
                elif "双" in item:
                    for i in range(int(weeks_pair[0]), int(weeks_pair[1]) + 1):
                        if i % 2 == 0:
                            week_list.append(i)
                else:
                    for i in range(int(weeks_pair[0]), int(weeks_pair[1]) + 1):
                        week_list.append(i)
            else:
                week_num = re.findall(r"(\d+)", item)
                if len(week_num) == 1:
                    week_list.append(int(week_num[0]))
        return week_list

class Choose(object):
    """选课类"""

    def __init__(self, cookies):
        self.login_url_nodomain = "/xtgl/login_slogin.html"
        self.headers = {
            "Referer": BASE_URL,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
        }
        self.timeout = 3
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = cookies

    def get_selected_courses(self, year: str, term: str):
        """获取已选课程信息"""
        try:
            url = urljoin(BASE_URL, "/xsxk/zzxkyzb_cxZzxkYzbChoosedDisplay.html?gnmkdm=N253512")
            term = str(int(term) ** 2 * 3)
            data = {
                "xkxnm": year,
                "xkxqm": term
            }
            req_selected = self.sess.post(
                url,
                data=data,
                headers=self.headers,
                cookies=self.cookies,
                timeout=self.timeout,
            )
            if req_selected.status_code != 200:
                return {"code": 2333, "msg": "教务系统挂了"}
            doc = pq(req_selected.text)
            if doc("h5").text() == "用户登录":
                return {"code": 1006, "msg": "未登录或已过期，请重新登录"}
            selected = req_selected.json()
            result = {
                "year": year,
                "term": term,
                "count": len(selected),
                "courses": [
                    {
                        "course_id": i.get("kch"),
                        "class_id": i.get("jxb_id"),
                        "do_id": i.get("do_jxb_id"),
                        "title": i.get("kcmc"),
                        "teacher_id": (re.findall(r"(.*?\d+)/", i.get("jsxx")))[0],
                        "teacher": (re.findall(r"/(.*?)/", i.get("jsxx")))[0],
                        "credit": float(i.get("xf", 0)),
                        "category": i.get("kklxmc"),
                        "capacity": int(i.get("jxbrs", 0)),
                        "selected_number": int(i.get("yxzrs", 0)),
                        # "place": self.get_place(i.get("jxdd")),
                        # "time": self.get_course_time(i.get("sksj")),
                        "optional": int(i.get("zixf", 0)),
                        "waiting": i.get("sxbj"),
                    }
                    for i in selected
                ],
            }
            return {"code": 1000, "msg": "获取已选课程成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取已选课程超时"}
        except (
                exceptions.RequestException,
                json.decoder.JSONDecodeError,
                AttributeError,
        ):
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试，若多次失败可能是系统错误维护或需更新接口"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": f"获取已选课程时未记录的错误：{str(e)}"}

    def get_can_choose_courses(self, start_page: str, end_page: str, key_word = None, head_data: dict = None):
        """获取板块课选课列表"""
        try:
            if head_data is None:
                # 获取head_data
                url_head = urljoin(
                    BASE_URL,
                    "/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default",
                )
                req_head_data = self.sess.get(
                    url_head,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=self.timeout,
                )
                if req_head_data.status_code != 200:
                    return {"code": 2333, "msg": "教务系统挂了"}
                doc = pq(req_head_data.text)
                if doc("h5").text() == "用户登录":
                    return {"code": 1006, "msg": "未登录或已过期，请重新登录"}
                if str(doc("div.nodata")) != "":
                    return {"code": 998, "msg": doc("div.nodata").text()}
                head_data = {}
                for head_data_content in doc("input[type='hidden']").items():
                    tag_id = head_data_content.attr("id")
                    tag_value = head_data_content.attr("value")
                    head_data[str(tag_id)] = str(tag_value)
                url_display = urljoin(BASE_URL, "/xsxk/zzxkyzb_cxZzxkYzbDisplay.html?gnmkdm=N253512")
                display_req_data = {
                    "xkkz_id": head_data["firstXkkzId"],
                    "xszxzt": head_data["xszxzt"],
                    "kspage": '0',
                    "jspage": '0'
                }
                req_display_data = self.sess.post(
                    url_display,
                    headers=self.headers,
                    data=display_req_data,
                    cookies=self.cookies,
                    timeout=self.timeout,
                )
                doc_display = pq(req_display_data.text)
                display_data = {}
                for display_data_content in doc_display("input[type='hidden']").items():
                    tag_name = display_data_content.attr("name")
                    tag_value = display_data_content.attr("value")
                    display_data[str(tag_name)] = str(tag_value)
                head_data.update(display_data)
            else:
                pass
            if head_data["iskxk"] != '1':
                return {"code": 1101, "msg": "当前不在可选时间内"}
            # 获取课程列表
            url_kch = urljoin(BASE_URL, "/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html?gnmkdm=N253512")
            kch_data = {
                # 以下是重要参数
                "xkxnm": head_data["xkxnm"],
                "xkxqm": head_data["xkxqm"],
                "kklxdm": head_data["firstKklxdm"],
                # "kspage": str(int(head_data["jspage"]) + 1),
                # "jspage": str(int(head_data["jspage"]) + int(head_data["xkmcjzxskcs"])),
                "kspage": start_page,
                "jspage": end_page,
                # 下面这一个参数是用于搜索词的
                "filter_list[0]": key_word if key_word != None else "",
                # 以下应该是无关紧要的参数
                "rwlx": head_data["rwlx"],
                "xkly": head_data["xkly"],
                "bklx_id": head_data["bklx_id"],
                "sfkkjyxdxnxq": head_data["sfkkjyxdxnxq"],
                "xqh_id": head_data["xqh_id"],
                "jg_id": head_data["jg_id_1"],
                "njdm_id_1": head_data["njdm_id_1"],
                "zyh_id_1": head_data["zyh_id_1"],
                "zyh_id": head_data["zyh_id"],
                "zyfx_id": head_data["zyfx_id"],
                "njdm_id": head_data["njdm_id"],
                "bh_id": head_data["bh_id"],
                "xbm": head_data["xbm"],
                "xslbdm": head_data["xslbdm"],
                "mzm": head_data["mzm"],
                "xz": head_data["xz"],
                "ccdm": head_data["ccdm"],
                "xsbj": head_data["xsbj"],
                "sfkknj": head_data["sfkknj"],
                "sfkkzy": head_data["sfkkzy"],
                "kzybkxy": head_data["kzybkxy"],
                "sfznkx": head_data["sfznkx"],
                "zdkxms": head_data["zdkxms"],
                "sfkxq": head_data["sfkxq"],
                "sfkcfx": head_data["sfkcfx"],
                "kkbk": head_data["kkbk"],
                "kkbkdj": head_data["kkbkdj"],
                "sfkgbcx": head_data["sfkgbcx"],
                "sfrxtgkcxd": head_data["sfrxtgkcxd"],
                "tykczgxdcs": head_data["tykczgxdcs"],
                "bbhzxjxb": head_data["bbhzxjxb"],
                "rlkz": head_data["rlkz"],
                "xkzgbj": head_data["xkzgbj"],
            }
            kch_res = self.sess.post(
                url_kch,
                headers=self.headers,
                data=kch_data,
                cookies=self.cookies,
                timeout=self.timeout,
            )
            jkch_res = kch_res.json()
            temp_list = jkch_res["tmpList"]
            if len(temp_list) == 0:
                return {"code": 999, "msg": "获取课程数量为0"}
            result = {
                "count": len(temp_list),
                "startPage": start_page,
                "endPage": end_page,
                "headData": head_data,
                "courses": [
                    {
                        "course_id": j["kch_id"],
                        "class_id": j.get("jxb_id"),
                        "class_name": j.get("jxbmc"),
                        "do_id": j.get("do_jxb_id"),
                        "title": j.get("kcmc"),
                        "credit": float(j.get("xf", 0)),
                        "selected_number": int(j.get("yxzrs", 0)),
                        "kklxdm": j.get("kklxdm", 0)
                    } for j in temp_list
                ],
            }
            return {"code": 1000, "msg": "获取板块课信息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取板块课信息超时"}
        except (
                exceptions.RequestException,
                json.decoder.JSONDecodeError,
                AttributeError,
        ):
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试，若多次失败可能是系统错误维护或需更新接口"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": f"获取板块课信息时未记录的错误：{str(e)}"}

    def get_single_course_class(self, course_id: str, selected_number:int, head_data: dict = None):
        """加载某门课程的教学班"""
        try:
            if head_data is None:
                # 获取head_data
                url_head = urljoin(
                    BASE_URL,
                    "/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default",
                )
                req_head_data = self.sess.get(
                    url_head,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=self.timeout,
                )
                if req_head_data.status_code != 200:
                    return {"code": 2333, "msg": "教务系统挂了"}
                doc = pq(req_head_data.text)
                if doc("h5").text() == "用户登录":
                    return {"code": 1006, "msg": "未登录或已过期，请重新登录"}
                if str(doc("div.nodata")) != "":
                    return {"code": 998, "msg": doc("div.nodata").text()}
                head_data = {}
                for head_data_content in doc("input[type='hidden']").items():
                    tag_id = head_data_content.attr("id")
                    tag_value = head_data_content.attr("value")
                    head_data[str(tag_id)] = str(tag_value)
                url_display = urljoin(BASE_URL, "/xsxk/zzxkyzb_cxZzxkYzbDisplay.html?gnmkdm=N253512")
                display_req_data = {
                    "xkkz_id": head_data["firstXkkzId"],
                    "xszxzt": head_data["xszxzt"],
                    "kspage": '0',
                    "jspage": '0'
                }
                req_display_data = self.sess.post(
                    url_display,
                    headers=self.headers,
                    data=display_req_data,
                    cookies=self.cookies,
                    timeout=self.timeout,
                )
                doc_display = pq(req_display_data.text)
                display_data = {}
                for display_data_content in doc_display("input[type='hidden']").items():
                    tag_name = display_data_content.attr("name")
                    tag_value = display_data_content.attr("value")
                    display_data[str(tag_name)] = str(tag_value)
                head_data.update(display_data)
            else:
                pass
            if head_data["iskxk"] != '1':
                return {"code": 1101, "msg": "当前不在可选时间内"}
            url_bkk = urljoin(BASE_URL, "/xsxk/zzxkyzbjk_cxJxbWithKchZzxkYzb.html?gnmkdm=N253512")
            bkk_data = {
                "bklx_id": head_data["bklx_id"],
                "xqh_id": head_data["xqh_id"],
                "njdm_id": head_data["njdm_id"],
                "xkxnm": head_data["xkxnm"],
                "xkxqm": head_data["xkxqm"],
                "kklxdm": head_data["firstKklxdm"],
                "kch_id": course_id,
                "xkkz_id": head_data["firstXkkzId"],
                "rwlx": head_data["rwlx"],
                "zyh_id": head_data["zyh_id"],
            }
            jxb_res = self.sess.post(
                url_bkk,
                headers=self.headers,
                data=bkk_data,
                cookies=self.cookies,
                timeout=self.timeout,
            )
            jxb_list = jxb_res.json()
            if len(jxb_list) == 0:
                return {"code": 999, "msg": "获取教学班数量为0"}
            result = {
                "count": len(jxb_list),
                "classes": []
            }
            for i in jxb_list:
                teacher_info = []
                for j in re.findall(r"(.*?\d+)/(.*?\w)/(\w+);?", i.get("jsxx")):
                    teacher_info.append({
                        "teacher_id": j[0],
                        "teacher_name": j[1],
                        "teacher_professional_ranks": j[2]
                    })
                result["classes"].append({
                    "course_id": course_id,
                    "teacher": teacher_info,
                    "teacher_text": i.get("jsxx"),
                    "course_college": i.get("kkxymc"),
                    "course_owner": i.get("kcgsmc"),
                    "course_category": i.get("kclbmc"),
                    "course_nature": i.get("kcxzmc"),
                    "teaching_model": i.get("jxms"),
                    "capacity": int(i.get("jxbrl", 0)),
                    "selected_number": selected_number,
                    "is_full": selected_number >= int(i.get("jxbrl", 0)),
                    "place": i.get("jxdd").split("<br/>")[0] if "<br/>" in i.get("jxdd") else i.get("jxdd"),
                    "time": "、".join(i.get("sksj").split("<br/>")) if "<br/>" in i.get("sksj") else i.get("sksj"),
                    "do_jxb_id": i.get("do_jxb_id"),
                    "jxb_id": i.get("jxb_id"),
                })
            return {"code": 1000, "msg": "获取板块课信息成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "获取教学班信息超时"}
        except (
                exceptions.RequestException,
                json.decoder.JSONDecodeError,
                AttributeError,
        ):
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试，若多次失败可能是系统错误维护或需更新接口"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": f"获取教学班信息时未记录的错误：{str(e)}"}

    def select_course(
            self,
            grade_id: str,
            course_id: str,
            do_id: str,
            year: str,
            term: str,
    ):
        """选课"""
        # TODO 接口测试通过，代码未测试
        try:
            url_select = urljoin(
                BASE_URL, "/xsxk/zzxkyzb_xkBcZyZzxkYzb.html?gnmkdm=N253512"
            )
            term = str(int(term) ** 2 * 3)
            select_data = {
                "jxb_ids": do_id,
                "kch_id": course_id,
                # 'rwlx': '3',
                # 'rlkz': '0',
                # 'rlzlkz': '1',
                # 'sxbj': '1',
                # 'xxkbj': '0',
                # 'cxbj': '0',
                "qz": "0",
                # 'xkkz_id': '9B247F4EFD6291B9E055000000000001',
                "xkxnm": year,
                "xkxqm": term,
                "njdm_id": grade_id,
                # 'kklxdm': str(kklxdm),
                # 'xklc': '1',
            }
            req_select = self.sess.post(
                url_select,
                headers=self.headers,
                data=select_data,
                cookies=self.cookies,
                timeout=self.timeout,
            )
            if req_select.status_code != 200:
                return {"code": 2333, "msg": "教务系统挂了"}
            doc = pq(req_select.text)
            if doc("h5").text() == "用户登录":
                return {"code": 1006, "msg": "未登录或已过期，请重新登录"}
            result = req_select.json()
            if result['flag'] == "1":
                return {"code": 1000, "msg": "选课成功", "data": result}
            else:
                return {"code": 1001, "msg": "选课失败", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "选课超时"}
        except (
                exceptions.RequestException,
                json.decoder.JSONDecodeError,
                AttributeError,
        ):
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试，若多次失败可能是系统错误维护或需更新接口"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": f"选课时未记录的错误：{str(e)}"}

    def cancel_course(self, course_id: str, do_id: str, year: str, term: str):
        """取消选课"""
        try:
            url_cancel = urljoin(
               BASE_URL, "/xsxk/zzxkyzb_tuikBcZzxkYzb.html?gnmkdm=N253512"
            )
            term = str(int(term) ** 2 * 3)
            cancel_data = {
                "jxb_ids": do_id,
                "kch_id": course_id,
                "xkxnm": year,
                "xkxqm": term,
                # "txbsfrl": "0"
            }
            req_cancel = self.sess.post(
                url_cancel,
                headers=self.headers,
                data=cancel_data,
                cookies=self.cookies,
                timeout=self.timeout,
            )
            if req_cancel.status_code != 200:
                return {"code": 2333, "msg": "教务系统挂了"}
            doc = pq(req_cancel.text)
            if doc("h5").text() == "用户登录":
                return {"code": 1006, "msg": "未登录或已过期，请重新登录"}
            result = {"status": re.findall(r"(\d+)", req_cancel.text)[0]}
            return {"code": 1000, "msg": "退课成功", "data": result}
        except exceptions.Timeout:
            return {"code": 1003, "msg": "选课超时"}
        except (
                exceptions.RequestException,
                json.decoder.JSONDecodeError,
                AttributeError,
        ):
            traceback.print_exc()
            return {"code": 2333, "msg": "请重试，若多次失败可能是系统错误维护或需更新接口"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 999, "msg": f"选课时未记录的错误：{str(e)}"}

# if __name__ == '__main__':
#     LG=Login()
#     # result=LG.login('20211101062','2001121..das')
#     result = LG.login('20211101052', 'zzx021121..')
#     # print(result)
#     cookies11 = result['data']['cookies']
#     IF=Info(cookies=cookies11)
#     # IF.getPersonInfo()
#     m=IF.getCollegeGradeList()
#     # print(m)
#     # n=IF.getMajorList(college_id="2021")
#     # print(n)
