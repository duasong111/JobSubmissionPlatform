from django.conf import settings
import hashlib

def md5(data_string):
    obj=hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    obj.update(data_string.encode('utf-8'))
    return obj.hexdigest()

#我要再写一个解密的，只是加密的可不行