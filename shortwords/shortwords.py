
from qqbot import _bot as bot
import requests
import re
import qface
import os
import time


class SendObj:
    """
    发送对象类（充当结构体233）
    """

    def __init__(self, buddy=(), group=(), discuss=()):
        self.buddy = buddy
        self.group = group
        self.discuss = discuss


class ShortWords:
    """
    【抽象类】使用qqbot实现发送微语的基类
    """

    def get_content(self):
        """
        【抽象方法】获取微语内容
        """
        raise NotImplementedError

    def send(self, qqNum, sendObj):
        """
        发送微语\n
        args:\n
            qqNum:发送者QQ号码
            sendObj:发送对象
        """
        if not isinstance(sendObj, SendObj):
            raise TypeError('sendObj should be SendObj Type,not ' + type(sendObj))
        bot.Login(['-q', '%s' % qqNum])
        mes = self.get_content()
        for bu in sendObj.buddy:
            bl = bot.List('buddy', str(bu))
            if bl:
                b = bl[0]
                bot.SendTo(b, mes)
        for gr in sendObj.group:
            bl = bot.List('group', str(gr))
            if bl:
                b = bl[0]
                bot.SendTo(b, mes)
        for dis in sendObj.discuss:
            bl = bot.List('discuss', str(dis))
            if bl:
                b = bl[0]
                bot.SendTo(b, mes)


class QShortWords(ShortWords):
    """
    增加了常用的信息爬取函数和常用格式符的ShortWord的子类
    """

    def __init__(self, mesFormat='#表情:(玫瑰)'):
        """
        实例化当前对象\n
        args:\n
            mesFormat:格式化的字符串，用于组织微语的排版，格式符见下\n
                #表情:(玫瑰 得意 鼓掌 卖萌 奋斗 喝彩 街舞...)\n
                #[今天|明天|后天]天气:[日期|高温|低温|风向|风力|类型]\n
            sendObj:发送对象，类型为 SendObj，默认为空
        """
        self.__mesFormat = mesFormat
        super().__init__()

    def get_content(self):
        """
        获取微语本体
        """
        def rap_weather(matched):
            sharp = matched.group(1)
            t = matched.group(2)
            ty = matched.group(3)
            if len(sharp) == 1:
                i = 0
                flag = ''
                if t == '今天':
                    i = 0
                elif t == '明天':
                    i = 1
                elif t == '后天':
                    i = 2
                if ty == '日期':
                    flag = 'date'
                elif ty == '高温':
                    flag = 'high'
                elif ty == '低温':
                    flag = 'low'
                elif ty == '风向':
                    flag = 'fengxiang'
                elif ty == '类型':
                    flag = 'type'
                return self.get_forecast_weather()[i][flag]
            else:
                return matched.group(0)[1:]

        def rap_random_face(matched):
            sharp = matched.group(1)
            lt = matched.group(2)
            lts = lt.split()
            avals = [l for l in lts if qface.getface(l) != None]
            if len(sharp) == 1 and len(avals) != 0:
                return qface.getfacebyran(avals)
            else:
                return matched.group(0)[1:]

        temp = re.sub('(#{1,})(今天|明天|后天)天气:(日期|高温|低温|风向|风力|类型)',
                      rap_weather, self.__mesFormat)
        return re.sub(r'(#{1,})表情:\(([^\)]*)\)', rap_random_face, temp)

    @staticmethod
    def get_forecast_weather(citycode=101200801):
        """
        获取天气预报信息\n
        args:\n
            citycode:欲获取天气预报的区域代码，默认为荆州区的区域代码\n
        return:\n
        [{'date': '2日星期一', 'high': '28℃', 'fengli': '<3级', 'low': '17℃', 'fengxiang': '西北风', 'type': '晴'},]
        """
        r = requests.get('http://wthrcdn.etouch.cn/weather_mini?citykey=%s' % citycode)
        r_json = r.json()
        forecast = r_json['data']['forecast']
        # 稍微处理下转义和去除些无用字符
        for f in forecast:
            f['high'] = f['high'][3:]
            f['low'] = f['low'][3:]
            f['fengli'] = f['fengli'][9:-3]
        return forecast


class TShortWords(QShortWords):
    """
    增加了小尾巴的QShortWord的子类
    """

    def __init__(self, mesFormat='#表情:(玫瑰)'):
        """
        实例化当前对象\n
        args:\n
            mesFormat:格式化的字符串，用于组织微语的排版，格式符见下\n
                #小尾巴:(E:\\TailPath|这是一条小尾巴~)
                #表情:(玫瑰 得意 鼓掌 卖萌 奋斗 喝彩 街舞...)\n
                #[今天|明天|后天]天气:[日期|高温|低温|风向|风力|类型]\n
            sendObj:发送对象，类型为 SendObj，默认为空
        """
        super().__init__(mesFormat)

    def get_content(self):
        def rap_tail(matched):
            sharp = matched.group(1)
            pathOrCot = matched.group(2)
            if len(sharp) == 1:
                tail = TShortWords.get_tail(pathOrCot)
                return pathOrCot if tail == None else tail
            else:
                return matched.group(0)[1:]
        return re.sub(r"(#{1,})小尾巴:\(([^\)]*)\)", rap_tail, super().get_content())

    @staticmethod
    def get_tail(parentPath):
        """
        从指定的父目录下获取相应的小尾巴
        失败返回 None
        args:
            parentPath:指定的父目录路径
        """
        def __getcontent(filePath):
            content = ''
            with open(filePath) as f:
                content = f.read()
                while len(content) > 120:
                    print('预定义的尾巴无效！请确保字数在120字以内！')
                    content = input('请直接在此终端输入小尾巴内容：\n')
            with open(filePath, 'w+') as f:
                f.write(content)
            return None if content == '' else content
        todayDat = time.localtime(time.time())
        if not os.path.exists(parentPath):
            return None
        txts = [file for file in os.listdir(parentPath) if os.path.splitext(file)[1] == '.txt']
        time_s = [time.strptime(s, '%Y-%m-%d.txt') for s in txts]
        if len(time_s) == 0:
            return None
        time_s.sort()     
        getPath = lambda timeData:time.strftime(os.path.join(parentPath, '%Y-%m-%d.txt'), timeData)
        todayTailFilePath = getPath(todayDat)
        # 先判断今天的尾巴文件是否存在
        if os.path.exists(todayTailFilePath):
            return __getcontent(todayTailFilePath)
        else:
            # 如果不存在，则首先比较一下今天的日期与文件列表中的最小日期（最过去时）
            if todayDat < time_s[0]:
                return None
            else:
                temp = [t for t in time_s if t < todayDat]
                temp.sort()
                return __getcontent(getPath(temp[len(temp) - 1]))
