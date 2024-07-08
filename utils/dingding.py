import json
from datetime import datetime

import requests

from a_songbo.binance_client.utils.lock import instance_synchronized


class Dingding:

    url = ('https://oapi.dingtalk.com/robot/send?access_token='
           '2b336337436ea0b4edb5c4117d584b01b613c9eaf102c284e27ae5cfb92d4b8b')

    @classmethod
    @instance_synchronized
    def send_msg(cls, text: str, isatall=False):
        # print('-----', datetime.now())
        # print(text)
        # print('-----')
        # return
        data = {
            "msgtype": "markdown",
            "markdown": {
                        "title": '## ',
                        "text": datetime.now().strftime('%Y-%m-%d %H:%M:%S  \n') + text
                    },
            "at": {
                "isAtAll": isatall
            }
        }

        requests.post(cls.url, headers={'content-type': "application/json"},
                      data=json.dumps(data))


if __name__ == '__main__':
    Dingding.send_msg(text="第一行  \n第二行")

