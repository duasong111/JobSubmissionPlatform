from napi import Login, Info, Choose
from pprint import pprint
import json
import base64
import sys
import os

sid = "20201101381"  # 学号
password = "512k_OME"  # 密码
mycookies = {
    "insert_cookie": "67313298",
    "JSESSIONID": "7C6843E5D1E4043EE23477B897DB7109"
}
test_year = "2022"  # 查询学年
test_term = "2"  # 查询学期（1-上|2-下）

func_class = sys.argv[1]
func = sys.argv[2]
try:
    method = sys.argv[3]
except IndexError:
    method = None

if __name__ == "__main__":
    if method != "cookies":
        lgn = Login()
        pre_login = lgn.login(sid, password)
        if pre_login["code"] == 1001:
            pre_dict = pre_login["data"]
            with open(os.path.abspath("temp.json"), mode="w", encoding="utf-8") as f:
                f.write(json.dumps(pre_dict))
            with open(os.path.abspath("kaptcha.png"), "wb") as pic:
                pic.write(base64.b64decode(pre_dict["kaptcha_pic"]))
            kaptcha = input("输入验证码：")
            result = lgn.loginWithKaptcha(
                pre_dict["sid"],
                pre_dict["csrf_token"],
                pre_dict["cookies"],
                pre_dict["password"],
                pre_dict["modulus"],
                pre_dict["exponent"],
                kaptcha,
            )
            if result["code"] != 1000:
                pprint(result)
                sys.exit()
            cookies = lgn.cookies
        elif pre_login["code"] == 1000:
            cookies = lgn.cookies
        else:
            pprint(pre_login)
            sys.exit()
    else:
        cookies = mycookies
    if func_class == "info":
        person = Info(cookies)
        if func == "person":
            result = person.getPersonInfo()
        elif func == "gradepdf":
            result = person.getGradePDF(sid)
            if result["code"] == 1000:
                with open(os.path.abspath("grade.pdf"), "wb") as pdf:
                    pdf.write(result["data"])
                    result = "已保存到本地"
        elif func == "schedulepdf":
            result = person.getSchedulePDF("自定义昵称", test_year, test_term)
            if result["code"] == 1000:
                with open(os.path.abspath("schedule.pdf"), "wb") as pdf:
                    pdf.write(result["data"])
                    result = "已保存到本地"
        elif func == "study":
            result = person.getStudy(sid)
        elif func == "gpa":
            result = person.getGPA()
        elif func == "msg":
            result = person.getMessage()
        elif func == "grade":
            result = person.getGrade(test_year, test_term)
        elif func == "schedule":
            result = person.getSchedule(test_year, test_term)
        elif func == "schedule-class":
            result = person.getScheduleByClass(test_year, test_term, "2020", "00001", "AEBA890EB3859C91E053F090C7DA7DCE")
        elif func == "class":
            result = person.getNowClass()
        elif func == "get-all-colleges":
            result = person.getCollegesList()
        elif func == "get-all-colleges-grade":
            result = person.getCollegeGradeList()
        elif func == "get-major-list":
            result = person.getMajorList("01", "2020")
        elif func == "get-class-list1":
            result = person.getClassList1("01", "2020")
        elif func == "get-class-list2":
            result = person.getClassList2("2021", "1", "01", "2020")
        elif func == "get-teaching-plan-grade-list":
            result = person.getTeachingPlanGradeList()
        elif func == "get-teaching-plan-colleges-list":
            result = person.getTeachingPlanCollegesList()
        elif func == "get-teaching-plan-major-list":
            result = person.getTeachingPlanMajorList('03', '2020')
        elif func == "get-teaching-plan-major-class-list":
            result = person.getTeachingPlanMajorClassList("AA0DF48EB8639D5EE053F090C7DA6030")
        elif func == "get-teaching-plan-major-direction-list":
            result = person.getTeachingPlanMajorDirectionList("A9FE49DA25337131E053F090C7DAFB96")
        elif func == "get-teaching-plan-major-course-info-list":
            result = person.getTeachingPlanMajorCourseInfoList("AA0DF48EB8639D5EE053F090C7DA6030")
        pprint(result if result is not None else "缺少具体参数")
    elif func_class == "choose":
        person = Choose(cookies)
        if func == "choosed":
            result = person.getChoosed(test_year, test_term)
        elif func == "block-course":
            result = person.get_selected_courses("2022", "2")
            # result = person.get_can_choose_courses("1", "10", "中国")
            # result = person.select_course("2020", "16410004", "3df652e6f5f06c2dd48a757b814cb3e90e447f0aa0a918a076ed65a4e1027d1f686693d6ccc7808dec68ad531ccdce6ffc48f7ba5ccdb37e62412e19747302fa1bc975ce0f96b68759c2adf0920925a4a89625917c83d993c1a6b12bcf0eb801b98275a9c66b0046130439063b295e3744b2b62a1b5aebfcbb45679011ad9fc6", "2022", "2")
            # result = person.cancel_course("16410004", "3df652e6f5f06c2dd48a757b814cb3e90e447f0aa0a918a076ed65a4e1027d1f686693d6ccc7808dec68ad531ccdce6ffc48f7ba5ccdb37e62412e19747302fa1bc975ce0f96b68759c2adf0920925a4a89625917c83d993c1a6b12bcf0eb801b98275a9c66b0046130439063b295e3744b2b62a1b5aebfcbb45679011ad9fc6", "2022", "2")
            # result = person.get_single_course_class("16410004", 740)
        pprint(result if result is not None else "缺少具体参数")
    else:
        pprint("缺少具体参数")