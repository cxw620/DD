# -*- coding: utf8 -*-
# 简简单单的DD程序, 基于腾讯云云函数
# 作者: 闻君心
# TODO: 加入订阅功能. 准备数据库.

# import base64
import random
import time
import json
import requests
import pytz
# from io import BytesIO
versionContent = "5.0"
updateContent = "重构程序,增加功能, 优化速度, 节约资源."

# import datetime
debugMode = True
# from functools import wraps

# stoutList = []
# def timethis(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         start = time.perf_counter()
#         r = func(*args, **kwargs)
#         end = time.perf_counter()
#         print('{}.{} : {}'.format(func.__module__, func.__name__, end - start))
#         return r
#     return wrapper

stoutList = []
UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.100.4758.11 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.131 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko Core/1.77.87.400 QQBrowser/10.9.4613.400"
]
headers_rad = {"User-Agent": random.sample(UA, 1)[0], 'Content-Type': 'application/json'}

# mid 107609241 直播间id:6461515青叶
# mid:378606811 直播间id:22341433 螃蟹那由
mids = [107609241, 378606811]
if debugMode:
    # 测试模式
    mids = [128552, 7375428, 1223206759]
# api地址. 参考https://github.com/SocialSisterYi/bilibili-API-collect
bili_live_api = "https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids"

# pushplus的token
push_plus_token = ""


# def urltobase64(url):
#     # 图片保存在内存
#     response = requests.get(url)
#     # 得到图片的base64编码
#     ls_f = base64.b64encode(BytesIO(response.content).read()).decode()
#     # 将base64编码进行解码
#     # imgdata = base64.b64decode(ls_f)
#     return ls_f


def time_str(t=""):
    # 时间函数模块
    if not t:
        t = time.time()
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


def push(__title__='ERROR', __content__={"提示信息": "错误"}, __group__="0000002", __token__=""):
    # 推送模块
    __content__ += "<div>" + \
        "<h3 style='font-size:bold'>DD-N Details</h3>" + \
        "<h4 style='font-size:bold'>程序版本 -> <h5>Ver " + versionContent + "</h5></h4>" + \
        "<h4 style='font-size:bold'>更新内容 -> <h5>" + updateContent + "</h5></h4>" + \
        "<h4 style='font-size:bold'>作者 -> <h5>Celestial Star" + "</h5></h4>" + \
        "<h4 style='font-size:bold'>信息发送时间 -> <h5>" + time_str() + "</h5></h4>" + \
        "</div>"

    # if debugMode:
    #     p_log("PUSH CALLBACK: " + str(__content__))
    #     return
    push_api = "https://www.pushplus.plus/send"
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
    p_log("PUSH CALLBACK: " + str(rc.text))
    return


def p_log(_data, _remind=False, _over=False):
    if debugMode:
        now_time = str(time_str(int(time.time())))
        if _remind:
            _remind = "[ERROR] "
        else:
            _remind = "[INFO] "
        if _over:
            for i in range(len(stoutList)):
                p_log(stoutList[i])
        else:
            _stout = _remind + now_time + "->" + str(_data)
            stoutList.append(_stout)
    return


def bili_gain(__mids__, __bili_live_api__, __retry_count__=0, __headers__=headers_rad):
    try:
        # 请求API
        if __retry_count__:
            p_log("尝试获取直播信息第" + str(__retry_count__) + "次")
        p_log({"uids": __mids__})
        live_status_res = requests.post(data=json.dumps({"uids": __mids__}), headers=__headers__, url=__bili_live_api__)
        live_status_dist = json.loads(live_status_res.text)
        # 判断是否正确请求, 手动抛出异常
        if live_status_dist['code'] != 0:
            raise NameError("B站API请求失败, API返回" + live_status_dist['message'])
        return_info = [__retry_count__]

        # 判断直播状态, 获取信息
        for i in range(len(__mids__)):
            temp_live_status_dist = live_status_dist["data"][str(__mids__[i])]
            # print(temp_live_status_dist["live_status"])
            # UP主
            name = temp_live_status_dist["uname"]
            if temp_live_status_dist["live_status"] == 1:

                # 直播开始的时间(时间戳)
                liveTimeStamp = int(temp_live_status_dist["live_time"])

                # 开播15分钟后就不提醒了.
                # if int(time.time()) - liveTimeStamp > 960:
                #     data = False
                #     return
                # 直播间名称
                liveName = temp_live_status_dist["title"]

                # 直播间地址, 备用后续开发, 需要时使用
                # liveURL = live_status_dist["data"]["live_room"]["url"]
                # 直播间人气
                liveOnline = str(temp_live_status_dist["online"])
                # 分区
                liveArea = temp_live_status_dist["area_v2_parent_name"] + " - " + temp_live_status_dist["area_v2_name"]

                # 标签
                liveTags = temp_live_status_dist["tags"] + " / " + temp_live_status_dist["tag_name"]
                if temp_live_status_dist["broadcast_type"] == 1:
                    liveType = "手机直播"
                else:
                    liveType = "电脑直播"
                # 直播封面图
                # liveCover = urltobase64(temp_live_status_dist["cover_from_user"])
                liveCover = temp_live_status_dist["cover_from_user"]
                # 直播截屏
                # liveShot = urltobase64(temp_live_status_dist["keyframe"])
                liveShot = temp_live_status_dist["keyframe"]
                # 输出.data:image/png;base64,
                push_content = "<div><h3 style='font-size:bold'>直播间信息(点我查看详情)" + "</h3>" + \
                    "<h4 style='font-size:bold'>直播间名称: <h5>" + liveName + "</h5></h4>" + \
                    "<h4 style='font-size:bold'>直播间人气: <h5>" + str(liveOnline) + "</h5></h4>" + \
                    "<h4 style='font-size:bold'>直播间开播时间: <h5>" + time_str(liveTimeStamp) + "</h5></h4>" + \
                    "<h4 style='font-size:bold'>直播间类型: <h5>" + liveType + "</h5></h4>" + \
                    "<h4 style='font-size:bold'>直播间分区: <h5>" + liveArea + "</h5></h4>" + \
                    "<h4 style='font-size:bold'>直播间标签: <h5>" + liveTags + "</h5></h4>" + \
                    "<h4 style='font-size:bold'>直播间封面图:<img src='" + liveCover + "' referrerpolicy='no-referrer'/></h4>" + \
                    "<h4 style='font-size:bold'>直播截图:<img src='" + liveShot + "' referrerpolicy='no-referrer'/></h4>" + \
                    "</div>"
                p_log(len(push_content))
                return_info.append([name, push_content])
            else:
                p_log(name + "未在直播")
        return return_info
    except:
        if __retry_count__ > 3:
            __retry_count__ = 0
            name = "ERROR"
            push_content = "用户直播信息获取失败, 请检查API等是否正常."
            push(name, push_content)
            return False
        else:
            __retry_count__ += 1
            time.sleep(random.randrange(1, 3, 1))
            return [__retry_count__]


def main_handler(event, context, _mids=mids):
    # ------------------程序主体----------------------------
    p_log(event["Time"] + " 开始执行自动任务")
    # 查询直播信息
    bili_res = bili_gain(_mids, bili_live_api)
    while True:
        if not bili_res:
            return False
        elif not bili_res[0]:
            for i in range(1, len(bili_res), 1):
                push("UP主[" + bili_res[i][0] + "]正在直播!", bili_res[i][1])
            break
        else:
            bili_res = bili_gain(_mids, bili_live_api, bili_res[0] + 1)

    # print(time.time())
    p_log("", False, True)
    return True
    # for serverless test only
    # _time = time_str()
    # p_log(push("TEST Serverless", push_q_content))


# 测试
event_input = {
    "Type": "Timer",
    "TriggerName": "EveryDay",
    "Time": "2019-02-21T11:49:00Z",
    "Message": "user define msg body"
}

main_handler(event_input, "")
