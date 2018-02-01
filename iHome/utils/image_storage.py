# -*- coding:utf-8 -*-

import qiniu

access_key = "yV4GmNBLOgQK-1Sn3o4jktGLFdFSrlywR2C-hvsW"
secret_key = "bixMURPL6tHjrb8QKVg2tm7n9k8C7vaOeQ4MEoeW"

bucket_name = "ihome"


def upload_image(data):
    """
    上传图片到七牛云的方法
    :param data: 图片数据
    :return:
    """

    q = qiniu.Auth(access_key, secret_key)
    token = q.upload_token(bucket_name)
    ret, info = qiniu.put_data(token, None, data)
    # 判断如果上传成功，那么就返回key
    if info.status_code == 200:
        return ret.get("key")
    else:
        # 如果上传失败，就抛出异常
        raise Exception("上传图片失败")


if __name__ == '__main__':
    file_name = raw_input("请输入图片地址：")
    with open(file_name, "rb") as f:
        upload_image(f.read())
