import datetime
import traceback
from urllib.parse import urljoin
from datetime import date, timedelta

import requests
from requests import exceptions
from pyquery import PyQuery as pq

WSYU_DK_BASE_URL = "http://dk.wsyu.edu.cn:8080"
TIMEOUT = 5


class PowerRate(object):
    """电费api"""

    def __init__(self):
        self.headers = requests.utils.default_headers()
        self.headers["Referer"] = "http://dk.wsyu.edu.cn"
        self.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        self.sess = requests.Session()
        self.sess.keep_alive = False
        self.cookies = {}

    def getArea(self):
        """获取区域信息"""
        url = urljoin(WSYU_DK_BASE_URL, "/icbs/PurchaseWebService.asmx/getAreaInfo")
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT
            )
            doc = pq(req_data.text.encode("utf-8"), parser="xml").remove_namespaces()
            if doc("resultInfo result").text() == "1":
                area_list = []
                for item in doc("areaInfoList areaInfo").items():
                    area_list.append({
                        "id": item.find("AreaID").text(),
                        "name": item.find("AreaName").text()
                    })
                return {"code": 1000, "msg": "获取宿舍区域成功", "data": area_list}
            else:
                return {"code": 999, "msg": "获取宿舍区域失败"}
        except Exception as e:
            return {"code": 999, "msg": "获取宿舍区域时未记录的错误：" + traceback.format_exc()}

    def getArchitecture(self, area_id: str):
        """获取建筑信息"""
        url = urljoin(WSYU_DK_BASE_URL, f"/icbs/PurchaseWebService.asmx/getArchitectureInfo?Area_ID={area_id}")
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT
            )

            doc = pq(req_data.text.encode("utf-8"), parser="xml").remove_namespaces()
            if doc("resultInfo result").text() == "1":
                architecture_list = []
                for item in doc("architectureInfoList architectureInfo").items():
                    architecture_list.append({
                        "id": item.find("ArchitectureID").text(),
                        "name": item.find("ArchitectureName").text(),
                        "floors": item.find("ArchitectureStorys").text()
                    })
                return {"code": 1000, "msg": "获取宿舍建筑成功", "data": architecture_list}
            else:
                return {"code": 999, "msg": "获取宿舍建筑失败"}
        except Exception as e:
            return {"code": 999, "msg": "获取宿舍建筑时未记录的错误：" + traceback.format_exc()}

    def getFloor(self, floors: str):
        """获取楼层信息"""
        try:
            return {"code": 1000, "msg": "获取宿舍楼层成功", "data": [str(i) for i in range(1, int(floors) + 1)]}
        except Exception as e:
            return {"code": 999, "msg": "获取楼层时未记录的错误：" + traceback.format_exc()}

    def getRoom(self, architecture_id: str, floor_id: str):
        """获取房间信息"""
        url = urljoin(WSYU_DK_BASE_URL,
                      f"/icbs/PurchaseWebService.asmx/getRoomInfo?Architecture_ID={architecture_id}&Floor={floor_id}")
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT
            )
            doc = pq(req_data.text.encode("utf-8"), parser="xml").remove_namespaces()
            if doc("resultInfo result").text() == "1":
                room_list = []
                for item in doc("roomInfoList RoomInfo").items():
                    room_list.append({
                        "id": item.find("RoomNo").text(),
                        "name": item.find("RoomName").text()
                    })
                return {"code": 1000, "msg": "获取宿舍房间成功", "data": room_list}
            else:
                return {"code": 999, "msg": "获取宿舍房间失败"}
        except Exception as e:
            return {"code": 999, "msg": "获取宿舍房间时未记录的错误：" + traceback.format_exc()}

    def getPowerRateSummary(self, room_id: str):
        """获取电表合计信息"""
        url = urljoin(WSYU_DK_BASE_URL, f"/icbs/PurchaseWebService.asmx/getMeterInfo?Room_ID={room_id}")
        try:
            req_data = self.sess.get(
                url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT
            )
            doc = pq(req_data.text.encode("utf-8"), parser="xml").remove_namespaces()
            if doc("resultInfo result").text() == "1":
                meter_list = []
                for item in doc("meterList MeterInfo").items():
                    meter_list.append({
                        "roomId": room_id,
                        "meterId": item.find("meterId").text(),
                        "address": item.find("meter_address").text(),
                        "type": item.find("conType").text(),
                    })
                data = meter_list[0]
                data["balance"] = self.__getBalanceByMeterId__(data["meterId"])
                data["dailyConsumption"] = self.__getDailyConsumptionByMeterId__(data["meterId"])
                data["monthConsumption"] = self.__getMonthConsumptionByMeterId__(data["meterId"])
                data["chargeOrder"] = self.__getChargeOrderByRoomId__(room_id)
                return {"code": 1000, "msg": "获取电表合计信息成功", "data": data}
            else:
                return {"code": 999, "msg": "获取电表合计信息失败"}
        except Exception as e:
            return {"code": 999, "msg": "获取电表合计信息时未记录的错误：" + traceback.format_exc()}

    def __getBalanceByMeterId__(self, meter_id: str):
        """内部方法，获取电表余额"""
        url = urljoin(WSYU_DK_BASE_URL, f"/icbs/PurchaseWebService.asmx/getReserveHKAM?AmMeter_ID={meter_id}")
        req_data = self.sess.get(
            url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT
        )
        doc = pq(req_data.text.encode("utf-8"), parser="xml").remove_namespaces()
        if doc("resultInfo result").text() == "1":
            data = {
                "balance": str(round(float(doc("remainPower").text()), 2)),
                "status": doc("state").text() + "--" + doc("valve").text(),
                "lastReadTime": doc("readTime").text()
            }
            return data
        else:
            return {}

    def __getDailyConsumptionByMeterId__(self, meter_id: str):
        """内部方法，获取每日消费"""
        end_date = date.today().strftime("%Y/%m/%d")
        start_date = (date.today() + timedelta(days=-15)).strftime("%Y/%m/%d")
        url = urljoin(WSYU_DK_BASE_URL,
                      f"/icbs/PurchaseWebService.asmx/getMeterDayValue?AmMeter_ID={meter_id}&startDate={start_date}&endDate={end_date}")
        req_data = self.sess.get(
            url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT
        )
        doc = pq(req_data.text.encode("utf-8"), parser="xml").remove_namespaces()
        if doc("resultInfo result").text() == "1":
            day_value_list = []
            for item in doc("dayValueInfoList DayValueInfo").items():
                day_value_list.append({
                    "electricityConsumption": item.find("dayValue").text(),
                    "expenses": item.find("dayUseMeony").text(),
                    "date": item.find("curDayTime").text()
                })
            return day_value_list
        else:
            return []

    def __getChargeOrderByRoomId__(self, room_id: str):
        """内部方法，获取充值订单"""
        end_date = date.today().strftime("%Y/%m/%d")
        start_date = (date.today() + timedelta(days=-90)).strftime("%Y/%m/%d")
        url = urljoin(WSYU_DK_BASE_URL,
                      f"/icbs/PurchaseWebService.asmx/getOrderList?studentId=&Room_ID={room_id}&startDate={start_date}&endDate={end_date}")
        req_data = self.sess.get(
            url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT
        )
        doc = pq(req_data.text.encode("utf-8"), parser="xml").remove_namespaces()
        if doc("resultInfo result").text() == "1":
            order_list = []
            for item in doc("orderInfoList OrderInfo").items():
                order_list.append({
                    "orderId": item.find("orderId").text(),
                    "date": datetime.datetime.strptime(item.find("orderTime").text(), "%Y/%m/%d %H:%M:%S").strftime(
                        "%Y-%m-%d"),
                    "money": item.find("orderMoney").text(),
                    "type": item.find("orderCashtype").text(),
                    "status": item.find("orderState").text()
                })
            return order_list
        else:
            return []

    def __getMonthConsumptionByMeterId__(self, meter_id: str):
        """内部方法，获取近六个月消费"""
        first_date_of_this_month = datetime.date.today().replace(day=1)
        end_month = (first_date_of_this_month - datetime.timedelta(days=1)).strftime("%Y%m")
        start_month = (first_date_of_this_month - timedelta(days=180)).strftime("%Y%m")
        url = urljoin(WSYU_DK_BASE_URL,
                      f"/icbs/PurchaseWebService.asmx/getMeterMonthValue?AmMeter_ID={meter_id}&startMonth={start_month}&endMonth={end_month}")
        req_data = self.sess.get(
            url, headers=self.headers, cookies=self.cookies, timeout=TIMEOUT
        )
        doc = pq(req_data.text.encode("utf-8"), parser="xml").remove_namespaces()
        if doc("resultInfo result").text() == "1":
            order_list = []
            for item in doc("MonthValueInfoList MonthValueInfo").items():
                order_list.append({
                    "month": item.find("The_Month").text(),
                    "expense": item.find("ZGross").text(),
                    "unitPrice": item.find("base_price").text() + "元/度"
                })
            return order_list
        else:
            return []


if __name__ == '__main__':
    PR = PowerRate()
    diqu = PR.getArea()  # h获取区域，得到教师和学生的的楼号id 输出可测试
    SD = PR.getArchitecture('0002')  # 获取学生寝室楼情况，若是教师，请传值为0001，进而得到floorid 输出可测试
    GF = PR.getFloor('7')  # 这个是输入楼层的层数 输出可测试
    GR = PR.getRoom('000007', '2')  # 这里传输的是建筑id和那个楼层id，可以输出所有的 输出可测试
    GPRS = PR.getPowerRateSummary('00001066')  # 获取房间的电费消费情况，同时为查余额提供meterID    6711.001066.1
    YE = PR.__getBalanceByMeterId__('6711.001066.1')  # 输入meterId来获取余额 输出可测试
    EveryConsume = PR.__getDailyConsumptionByMeterId__('6711.001066.1')  # 通过meterId来显示每日消费，没有房间号详细
    SixMonthConsumer = PR.__getMonthConsumptionByMeterId__('6711.001066.1') #输出可测试
    orders = PR.__getChargeOrderByRoomId__('00001066')  # 输入的是房间的id来查询电费订单情况

    # print(orders)  # 打印测试输出