# -*- coding: utf-8 -*-

import request
import config
import time
import threading
from datetime import datetime

"""
目前仅支持【无需选座】的项目
"""


class Config:
    show_id = config.show_id
    session_id = config.session_id
    buy_count = config.buy_count
    deliver_method = config.deliver_method
    seat_plan_id = None
    seat_plan_ids = config.seat_plan_ids
    seat_plan_price = 0
    seat_plan_prices = config.seat_plan_prices
    push_token = config.push_token
    start_time = config.start_time


class Script(threading.Thread):

    def __init__(self, token, push_flag):
        threading.Thread.__init__(self)
        self.token = token
        self.push_flag = push_flag

    def run(self):
        self.init()

    def init(self):
        print(f"{self.push_flag} init")
        # 获取观演人信息
        self.audiences = request.get_audiences(self.token)
        print("audiences:")
        print(self.audiences)
        self.audience_ids = [self.audiences[i]["id"] for i in range(Config.buy_count)]

        # 获取默认收货地址
        self.address = request.get_address(self.token)
        print("address:")
        print(self.address)

        # 获取快递费用
        self.express_fee = request.get_express_fee(
            Config.show_id,
            Config.session_id,
            Config.seat_plan_ids[0],
            Config.seat_plan_prices[0],
            Config.buy_count,
            self.address["locationId"],
            self.token,
        )
        print("express_fee:")
        print(self.express_fee)

        # 设置要执行的特定毫秒时间
        date_format = "%Y-%m-%d %H:%M:%S.%f"
        target_time = datetime.strptime(Config.start_time, date_format)
        target_millisecond = int(
            time.mktime(target_time.timetuple()) * 1000 + target_time.microsecond / 1000
        )
        current_millisecond = int(round(time.time() * 1000))
        wait_millisecond = target_millisecond - current_millisecond
        if wait_millisecond > 0:
            time.sleep(wait_millisecond / 1000)
        self.doing()

    def doing(self):
        print(f"{self.push_flag} doing")

        try:
            threading.Thread(
                target=request.notification,
                args=(Config.push_token, self.push_flag + "开始了！"),
            ).start()
        except Exception as e:
            print(e)

        try:
            last_index = len(Config.seat_plan_ids) - 1
            # 直接冲一下最贵的
            threading.Thread(
                target=self.postOrder,
                args=(
                    Config.seat_plan_ids[last_index],
                    Config.seat_plan_prices[last_index],
                ),
            ).start()
        except Exception as e:
            print(e)

        while True:
            try:
                self.seat_counts = request.get_seat_count(
                    Config.show_id, Config.session_id
                )
                print("seat_counts")
                print(self.seat_counts)
                for i in self.seat_counts:
                    try:
                        seat_plan_id_index = Config.seat_plan_ids.index(i["seatPlanId"])
                    except Exception as e:
                        continue
                    if seat_plan_id_index > 0 and i["canBuyCount"] >= Config.buy_count:
                        self.postOrder(
                            Config.seat_plan_ids[seat_plan_id_index],
                            Config.seat_plan_prices[seat_plan_id_index],
                        )
            except Exception as e:
                print("Exception")
                print(e)
            time.sleep(1)

    def postOrder(self, seat_plan_id, seat_plan_price: int):
        deliver_method = "EXPRESS"
        # 获取默认收货地址
        # address = request.get_address()
        address_id = self.address["addressId"]  # 地址id
        location_city_id = self.address["locationId"]  # 460102
        receiver = self.address["username"]  # 收件人
        cellphone = self.address["cellphone"]  # 电话
        detail_address = self.address["detailAddress"]  # 详细地址

        # 下单
        result = request.create_order(
            Config.show_id,
            Config.session_id,
            seat_plan_id,
            seat_plan_price,
            Config.buy_count,
            deliver_method,
            self.express_fee["priceItemVal"],
            receiver,
            cellphone,
            address_id,
            detail_address,
            location_city_id,
            self.audience_ids,
            self.token,
        )
        if result["statusCode"] == 200:
            request.notification(Config.push_token, self.push_flag + "抢到了！")
            return True
        return False

    def print(self, message):
        print(f"[{self.push_flag}] {message}")


thread_list = []
for k, v in config.token.items():
    print(f"k={k} start")
    push_flag = k
    token = v
    thread = Script(token, push_flag)
    thread.start()
    thread_list.append(thread)

for item in thread_list:
    print(f"k={k} join")
    item.join()

while True:
    time.sleep(1)
