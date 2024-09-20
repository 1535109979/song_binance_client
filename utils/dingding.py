import json
from datetime import datetime

import requests

from song_binance_client.utils.lock import instance_synchronized


class Dingding:

    url = ('https://oapi.dingtalk.com/robot/send?access_token=71652eb274cd6a8cca66983528c87d0ae85467b3af5920f6c2f357f6127dab55')

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

