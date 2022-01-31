# coding:utf-8
# 简简单单的DD程序, 借助腾讯云云函数执行.
# 作者: 闻君心
# 20220131


import requests
import random
import json
import base64
import time

# mid 107609241 直播间id:6461515青叶
# mid:378606811 直播间id:22341433 螃蟹那由
mids = ["107609241", "378606811"]
ids = ["6461515", "22341433"]

# api地址. 参考https://github.com/SocialSisterYi/bilibili-API-collect
bili_live_api = "api.bilibili.com/x/space/acc/info"
bili_live_api_add = "api.live.bilibili.com/room/v1/Room/room_init"

# pushplus的token. Line85请同步填上默认token.
push_plus_token = ""

# 随机UA
UA = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.100.4758.11 Safari/537.36",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.131 Safari/537.36",
      "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko Core/1.77.87.400 QQBrowser/10.9.4613.400"]
headers_rad = {
    "User-Agent": random.sample(UA, 1)[0], 'Content-Type': 'application/json'}


def bili_gain(__mid__, __id__, __bili_live_api__, __bili_live_api_add__, __push_plus_token__=push_plus_token, __headers__=headers_rad, usehttps=False):
    if usehttps:
        __bili_live_api__ = "https://" + __bili_live_api__
        __bili_live_api_add__ = "https://" + __bili_live_api_add__
    else:
        __bili_live_api__ = "http://" + __bili_live_api__
        __bili_live_api_add__ = "http://" + __bili_live_api_add__
    live_status_res = requests.get(
        headers=__headers__, url=__bili_live_api__ + "?mid=" + __mid__, timeout=10)
    live_status_res_add = requests.get(
        headers=__headers__, url=__bili_live_api_add__ + "?id=" + __id__, timeout=10)
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
            nowTimeArray = time.localtime(nowTimeStamp)
            nowTime = time.strftime("%Y年%m月%d日 %H:%M:%S", nowTimeArray)
            liveTimeStamp = int(liveTimeStamp)
            liveTimeArray = time.localtime(liveTimeStamp)
            liveTime = time.strftime("%Y年%m月%d日 %H:%M:%S", liveTimeArray)
            # 输出.
            push_content = "<div>开播信息: "+name+"<div>直播间名称: "+liveName+"</div><div>直播间地址: "+liveURL+"</div><div>直播间开播状态: " + \
                str(isLive)+"</div><div>直播间人气: "+str(liveOnline)+" </div><div>直播间开播时间: " + \
                liveTime+"</div><div>信息发送时间: "+nowTime+"</div></div>"
            return name, push_content
        else:
            return False
    except:
        name = "ERROR"
        push_content = "ID为" + __mid__ + "的用户的直播信息获取失败, 请检查API等是否正常."
        return name, push_content


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
    return rc.status_code


def cvcover(url, headers):
    r = requests.get(url, headers=headers)
    with open("pic.jpg", "wb") as file:
        file.write(r.content)
        file.close()
    f = open("pic.jpg", "rb")
    res = f.read()
    result = base64.b64encode(res)
    f.close()
    return result


# ------------------程序主体----------------------------
# 消息发送队列, 第一个是up主的名字, 第二个是内容, json格式.
push_q_name = []
push_q_content = {}
if len(ids) != len(mids):
    mids = ["107609241", "378606811"]
    ids = ["6461515", "22341433"]
    q_length = 2
else:
    q_length = len(mids)
for i in range(q_length):
    bili_res = bili_gain(mids[i], ids[i], bili_live_api, bili_live_api_add)
    if bili_res:
        push_q_name.append(bili_res[0])
        push_q_content = bili_res[1] + "<br>" + push_q_content
if push_q_name and push_q_content:
    push_q_name_total = ''.join(str(i) for i in push_q_name) + "正在直播!"
    push(push_q_name_total, push_q_content)
