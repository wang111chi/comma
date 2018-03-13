#!/usr/bin/env python
# -*- coding: utf-8 -*-

# put common default settings shared by all applications here

from base import constant as const

DEBUG = True
ENCODING = 'utf8'
DEBUG_PORT = 5000
HOME_URL = ''
API_URL = ''
DATABASE_URL = ('mysql+mysqlconnector://bigdata:Comma_2018@'
                'rm-wz99uqudq1rk4ep9o.mysql.rds.aliyuncs.com:3306/csys')
STATIC_URL_PATH = '/static'

# 前置机相关配置
PP_SERVER_HOST = '127.0.0.1'
PP_SERVER_PORT = 31001
PP_SERVER_SOCK_TIMEOUT = 30.0
PP_SERVER_FAKE = True

# API接口是否需要对参数进行加密
API_PARAM_ENCRYPT = False

# Logging配置
LOGGING_CONFIG = [
    ["cgi-log", "cgi.log", "debug"],
    ["response-log", "response.log", "debug"],

    ["tools-log", "tools.log", "debug"],
    ["task-log", "task.log", "debug"],
    ["pp-interface-log", "pp-interface.log", "debug"],
    ["batch-pay-interface-log", "batch-pay-interface.log", "debug"],
    ["bank-statement-log", "bank-statement.log", "debug"],
]

REDIS = {
    "host": "redis",
    "port": 6379,
    "db": 0,
}

# API不用解密和验签的客户端IP
CLIENT_IP_WHITELIST = ()

# sentry
SENTRY_LOGGING_ENABLED = False
SENTRY_CLIENT_KEY = 'sentry client key'

# 系统邮件SMTP设置
SYS_EMAIL_FROM = 'sys@xxx.com'
SYS_EMAIL_SMTP_HOST = 'mail.xxx.com'
SYS_EMAIL_SMTP_PORT = 0
SYS_EMAIL_SMTP_USER = 'user'
SYS_EMAIL_SMTP_PASSWD = 'passwd'

# 优惠券活动折扣中, 银行承担的百分数
DISCOUNT_RATIO_BANK = {'00179972003': 50, '00179972002': 50, '00204010010': 10}
