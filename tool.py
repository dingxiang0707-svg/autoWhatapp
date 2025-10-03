import os
import configparser
from asyncio.log import logger
from base64 import b64encode, b64decode
from hashlib import md5
from pyDes import des, CBC, PAD_PKCS5
import json

appCode = "11111111"
secretKey = b"uYMGr8eU"



#des加密
def triple_des_encrypt(data, timeline):
    signature = generate_signature(data, timeline)
    #print('Signature:', signature)

    dataToSend = json.dumps(data, separators=(",", ":"))
    message = {"data": dataToSend, "sign": signature}


    pson = json.dumps(message, separators=(",", ":"))
    # pson = str(message)
    data = bytes(pson, "utf-8")
    
    IV = bytearray()
    IV.append(0x12)
    IV.append(0x34)
    IV.append(0x56)
    IV.append(0x78)
    IV.append(0x90)
    IV.append(0xAB)
    IV.append(0xCD)
    IV.append(0xEF)

    k = des(
        secretKey,
        CBC,
        IV,
        pad=None,
        padmode=PAD_PKCS5
    )
    d = k.encrypt(data)
    return b64encode(d).decode("utf-8")

#des解密
def triple_des_decrypt(message):
    pson = json.dumps(message, separators=(",", ":"))
    # pson = str(message)
    data = bytes(pson, "utf-8")

    IV = bytearray()
    IV.append(0x12)
    IV.append(0x34)
    IV.append(0x56)
    IV.append(0x78)
    IV.append(0x90)
    IV.append(0xAB)
    IV.append(0xCD)
    IV.append(0xEF)

    k = des(
        secretKey,
        CBC,
        IV,
        pad=None,
        padmode=PAD_PKCS5
    )
    aa = b64decode(data)
    d = k.decrypt(aa, padmode=PAD_PKCS5)
   

    return d


def generate_signature(message, timeline):
    secretKey = "uYMGr8eU"
    logger.info(f"timeline: {timeline}")
    logger.info(f"secretKey: {secretKey}")
    logger.info(f"message: {message}")
    dumped_message = json.dumps(message, separators=(",", ":"))
    key_before_hashing = timeline + secretKey + dumped_message
    key_before_hashing = bytes(key_before_hashing, "utf-8")
    logger.info(f"before md5: {key_before_hashing}")
    sig = md5(key_before_hashing).hexdigest()
    logger.info(f"Signature: {sig}")
    return sig
        

def getConfig(section, key):
    config = configparser.ConfigParser()
    path = os.path.split(os.path.realpath(__file__))[0] + '/sp_confing.ini'
    config.read(path,encoding="utf-8")
    return config.get(section, key)


def setConfig(section, key , vaule):
    config = configparser.ConfigParser()
    path = os.path.split(os.path.realpath(__file__))[0] + '/sp_confing.ini'
    config.read(path,encoding="utf-8")
    config.set(section, key, vaule)
    with open(path, 'w+') as configfile:
        config.write(configfile)
    # return config.write(section, key)