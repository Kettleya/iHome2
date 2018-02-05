# -*- coding:utf-8 -*-
from iHome.api_1_0 import api
from iHome.utils.common import login_required


@api.route('/orders',methods=['POST'])
@login_required
def make_orders():
    """
    1.获取参数并校验
    2.从数据库中查询房屋状态(是否已被预定)
    3.如果未被预定,则创建订单及相关数据
    4.将数据保存到数据库
    5.给出响应
    :return:
    """