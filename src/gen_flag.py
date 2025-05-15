import hmac
import base64
import hashlib

flag = "ITSEC{{{0}}}"


def gen_flag(user: str, secret: str):
    hexdigest = hmac.new(
        secret.encode(), msg=user.encode(), digestmod=hashlib.sha256
    ).hexdigest()
    return flag.format(hexdigest)


def gen_flag_base64(user: str, secret: str):
    digest = hmac.new(
        secret.encode(), msg=user.encode(), digestmod=hashlib.sha256
    ).digest()
    return flag.format(base64.b64encode(digest).decode())
