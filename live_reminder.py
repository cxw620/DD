# -*- coding: utf8 -*-
# 简简单单的DD程序, 基于腾讯云云函数
# 作者: 闻君心

import requests
import random
import json
import base64
import time
import pytz
import datetime

# 程序版本号
versionContent = "V2.3"
updateContent = "修正直播开始后重复推送的问题, 修正API访问失败不重试的问题."
# mid 107609241 直播间id:6461515青叶
# mid:378606811 直播间id:22341433 螃蟹那由
mids = ["107609241", "378606811"]
ids = ["6461515", "22341433"]

# api地址. 参考https://github.com/SocialSisterYi/bilibili-API-collect
bili_live_api = "api.bilibili.com/x/space/acc/info"
bili_live_api_add = "api.live.bilibili.com/room/v1/Room/room_init"

# pushplus的token
push_plus_token = ""

# 随机UA
UA = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.100.4758.11 Safari/537.36",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.131 Safari/537.36",
      "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko Core/1.77.87.400 QQBrowser/10.9.4613.400"]
headers_rad = {
    "User-Agent": random.sample(UA, 1)[0], 'Content-Type': 'application/json'}

# 时间函数模块


def time_str(t=""):
    if not t:
        t = int(time.time())
    try:
        t = int(t)
    except:
        # 如果int失败估计这是字符串.
        try:
            t = int(time.mktime(time.strptime(t, "%Y-%m-%dT%H:%M:%SZ")))
        except:
            # 还不是就返回空字符串
            return ""
    dt = pytz.datetime.datetime.fromtimestamp(t, pytz.timezone('PRC'))
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')


def bili_gain(__mid__, __id__, __bili_live_api__, __bili_live_api_add__, __retry_count__=0, __headers__=headers_rad, usehttps=False):

    if usehttps:
        __bili_live_api__ = "https://" + __bili_live_api__
        __bili_live_api_add__ = "https://" + __bili_live_api_add__
    else:
        __bili_live_api__ = "http://" + __bili_live_api__
        __bili_live_api_add__ = "http://" + __bili_live_api_add__
    # 尝试访问API, 失败就重试
    try:
        live_status_res = requests.get(
            headers=__headers__, url=__bili_live_api__ + "?mid=" + __mid__, timeout=10)
        live_status_res_add = requests.get(
            headers=__headers__, url=__bili_live_api_add__ + "?id=" + __id__, timeout=10)
    except:
        if __retry_count__ > 3:
            tempRetryCount = 0
            name = "ERROR"
            push_content = "ID为" + __mid__ + "的用户的直播信息获取失败, 请检查API等是否正常."
            return name, push_content, tempRetryCount
        else:
            tempRetryCount = __retry_count__ + 1
            name = ""
            push_content = ""
            time.sleep(random.randrange(3, 10, 1))
            # 会不会死循环(笑)
            return name, push_content, tempRetryCount
    # 请求比利比利接口
    try:
        live_status_dist = json.loads(live_status_res.text)
        live_status_add_dist = json.loads(live_status_res_add.text)
        # UP主
        name = live_status_dist["data"]["name"]
        # 直播状态
        isLive = live_status_dist["data"]["live_room"]["liveStatus"]
        # 直播间名称
        liveName = live_status_dist["data"]["live_room"]["title"]
        # 直播间封面图, 弃用
        livePicURL = live_status_dist["data"]["live_room"]["cover"]
        # 直播间地址
        liveURL = live_status_dist["data"]["live_room"]["url"]
        # 直播间人气
        liveOnline = live_status_dist["data"]["live_room"]["online"]
        # 直播开始的时间(时间戳)
        liveTimeStamp = live_status_add_dist["data"]["live_time"]

        if isLive == 1:
            # 处理原始数据
            # livePicB64 = cvcover(livePicURL, headers_rad) # 弃用
            nowTimeStamp = int(time.time())
            liveTimeStamp = int(liveTimeStamp)
            # 开播15分钟后就不提醒了.
            if nowTimeStamp - liveTimeStamp > 960:
                return False
            # 输出.
            push_content = "<div>开播信息: "+name+"<div>直播间名称: "+liveName+"</div><div>直播间地址: "+liveURL+"</div><div>直播间开播状态: " + \
                str(isLive)+"</div><div>直播间人气: "+str(liveOnline)+" </div><div>直播间开播时间: " + \
                time_str(liveTimeStamp)+"</div><div>信息发送时间: " + \
                time_str(nowTimeStamp)+"</div></div>"
            return name, push_content
        else:
            return False
    except:
        if __retry_count__ > 3:
            tempRetryCount = 0
            name = "ERROR"
            push_content = "ID为" + __mid__ + "的用户的直播信息获取失败, 请检查API等是否正常."
            return name, push_content, tempRetryCount
        else:
            tempRetryCount = __retry_count__ + 1
            name = ""
            push_content = ""
            time.sleep(random.randrange(3, 10, 1))
            # 会不会死循环(笑)
            return name, push_content, tempRetryCount


def push(__title__='ERROR: 系统通知', __content__="程序错误, 请排查.", __group__="10001", __token__=""):
    push_api = "http://pushplus.hxtrip.com/send"
    __push_data__ = {
        "token": __token__,
        "title": __title__,
        "content": __content__,
        "topic": __group__,
        "template": "html"
    }
    __push_body__ = json.dumps(__push_data__).encode(encoding='utf-8')
    __headers__ = {'Content-Type': 'application/json'}
    rc = requests.post(push_api, data=__push_body__, headers=__headers__)
    return rc.text


# def cvcover(url, headers):
#     r = requests.get(url, headers=headers)
#     with open("pic.jpg", "wb") as file:
#         file.write(r.content)
#         file.close()
#     f = open("pic.jpg", "rb")
#     res = f.read()
#     result = base64.b64encode(res)
#     f.close()
#     return result


def main_handler(event, context, _ids=ids, _mids=mids):
    # ------------------程序主体----------------------------
    # 消息发送队列, 第一个是up主的名字, 第二个是内容, json格式.
    print(event["Time"] + " 开始执行自动任务")
    push_q_name = []
    push_q_content = "<div>Powered by 天极星</div><div>简简单单的DD程序, 基于腾讯云云函数</div><div>版本号: " + versionContent + \
        "</div><div>更新说明: " + updateContent + \
        "</div><div>" + time_str(event["Time"]) + "</div>"
    # 判断输入数据合法性
    if len(_ids) != len(_mids):
        _mids = ["107609241", "378606811"]
        _ids = ["6461515", "22341433"]
        q_length = 2
        _time = time_str()
        push_q_content = "提供的UUID和直播间ID不匹配. 已使用默认值" + push_q_content
    else:
        q_length = len(_mids)
    # 查询直播信息
    for i in range(q_length):
        bili_res = bili_gain(
            _mids[i], _ids[i], bili_live_api, bili_live_api_add)
        #  腾讯云函数:'bool' object is not subscriptable
        if not bili_res:
            return True
        
        if bili_res[2] != 0:
            bili_res = bili_gain(
                _mids[i], _ids[i], bili_live_api, bili_live_api_add, bili_res[2])
        else:
            push_q_name.append(bili_res[0])
            push_q_content = bili_res[1] + "<br>" + push_q_content
    if push_q_name and push_q_content:
        push_q_name_total = ''.join(str(i) for i in push_q_name) + "正在直播!"
        push_code = push(push_q_name_total, push_q_content)
        _time = time_str()
        print(_time + " Push Plus推送网页代码: " + push_code)
    # for test only
    # _time = timeGet()
    # print(push_q_content)
    # push("TEST Serverless", push_q_content)
