import base64
import time
import traceback

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from authlib.jose import jwt
from authlib.jose.errors import *

_issuer = "https://mapotofu.cn"  # 发布者
_expire_days = 24 * 60 * 60 * 60  # 60天
_public_key_pass = "utils/keys/rsa_public_key_pass.pem"
_private_key_pass = "utils/keys/rsa_private_key_pass.pem"
_public_key = "utils/keys/rsa_public_key.pem"
_private_key = "utils/keys/rsa_private_key.pem"


class TokenGenerate:
    def __init__(self, user_id: str, user_password: str, user_group: str):
        # 明文密码
        self.rawPassword = user_password
        # Header部分数据
        self.encodeHeader = {
            'alg': 'RS256'
        }
        # Payload部分数据
        self.encodePayload = {
            "iss": _issuer,
            "iat": int(time.time()),  # 发布时间
            "nbf": int(time.time()),  # 使用时间（不能早于这个时间）
            "exp": int(time.time() + _expire_days),  # 销毁时间
            "data": {
                "uid": user_id,
                "upass": self._encrypt_password(),
                "uGroup": user_group
            }
        }

    def _encrypt_password(self):
        """ 加密密码 """
        try:
            with open(_public_key_pass) as f:
                cipher = Cipher_pkcs1_v1_5.new(RSA.importKey(f.read()))
                cipher_text = base64.b64encode(cipher.encrypt(self.rawPassword.encode('utf-8')))
            return cipher_text.decode('utf-8')
        except Exception as e:
            return "error"

    def generate_token(self):
        """
        generate_token() -> dict

        返回生成token的结果
        字典内包含三个值：token：完整token，iat：生成时间，exp：到期时间
        """
        try:
            with open(_private_key, encoding="utf-8") as f:
                s = jwt.encode(self.encodeHeader, self.encodePayload, f.read())
                result = {
                    "token": s.decode('utf-8'),
                    "iat": self.encodePayload["iat"],
                    "exp": self.encodePayload["exp"]
                }
                return {"code": 200, "msg": "成功", "data": result}
        except Exception as e:
            return {"code": 400, "msg": "未知错误:{}".format(traceback.format_exc())}


class TokenValidate:
    def __init__(self, token: str):
        self.token = token.encode()
        self.claims = {}

    def validate_token(self):
        """
        validate_token() -> dict

        返回验证token的结果
        字典内包含解密后的原token
        """
        try:
            with open(_public_key, encoding="utf-8") as fp:
                claims = jwt.decode(self.token, fp.read())
                self.claims = claims
                claims.validate()
            return {"code": 200, "msg": "成功", "data": claims}
        except InvalidClaimError as e:
            return {"code": 401, "msg": "无效的%s参数".format(e.error)}
        except ExpiredTokenError as e:
            return {"code": 402, "msg": "Token过期", "data": claims}
        except Exception as e:
            return {"code": 400, "msg": "未知错误:{}".format(traceback.format_exc())}

    def decrypt_userinfo(self):
        """
        decrypt_userinfo() -> dict

        返回用户名和密码
        字典内包含两个值：uid：学号/教工号，upass密码
        """
        try:
            with open(_private_key_pass) as f:
                cipher = Cipher_pkcs1_v1_5.new(RSA.importKey(f.read()))
                password = cipher.decrypt(base64.b64decode(self.claims["data"]["upass"]), "fail")
            result = {
                "uid": self.claims["data"]["uid"],
                "upass": password.decode('utf-8')
            }
            return {"code": 200, "msg": "成功", "data": result}
        except Exception as e:
            return {"code": 400, "msg": "未知错误:{}".format(traceback.format_exc())}
