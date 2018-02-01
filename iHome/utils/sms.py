#coding=gbk

#coding=utf-8

#-*- coding: UTF-8 -*-  

from iHome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

#主帐号
accountSid= '8aaf0708612c8039016141374c22053a';

#主帐号Token
accountToken= '5ee7b269dbcb4dc398069c0675e4e8b6';

#应用Id
appId='8aaf0708612c8039016141374c940541';

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com';

#请求端口 
serverPort='8883';

#REST版本号
softVersion='2013-12-26';

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
  # @param $tempId 模板Id

class CCP(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            cls._instance.rest = REST(serverIP, serverPort, softVersion)
            cls._instance.rest.setAccount(accountSid, accountToken)
            cls._instance.rest.setAppId(appId)
        return cls._instance

    def send_template_sms(self, to, datas, temp_id):
        result = self.rest.sendTemplateSMS(to, datas, temp_id)

        status_code = result.get("statusCode")

        if status_code == "000000":

            return 1
        else:

            return 0


if __name__ == '__main__':
    print CCP().send_template_sms("", ["888888", "5"], "1")
