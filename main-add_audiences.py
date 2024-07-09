# -*- coding: utf-8 -*-

import request
import config

for account, token in config.token.items():
    get_audiences_result = request.get_audiences(token)
    print("get_audiences_result=" + str(get_audiences_result))
    get_audiences_user_list = []
    for item in get_audiences_result:
        get_audiences_user_list.append(item["name"])

    for name, idnumber in config.audiences.items():
        if name not in get_audiences_user_list:
            add_audiences_result = request.add_audiences(token, name, idnumber)
