#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import datetime
from decimal import Decimal
import operator
import urllib
import socket
import struct
import hashlib
from unittest import mock
from base64 import b64encode
from base64 import b64decode
import csv
import fcntl
import smtplib
from email.message import EmailMessage

from sqlalchemy import and_
# from Crypto.PublicKey import RSA
# from Crypto.Cipher import PKCS1_v1_5
# from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
# from Crypto.Hash import SHA
from base import db
from openpyxl import Workbook
from io import BytesIO

import config
from base import constant as const


def sed_file(old_str_list, new_str_list, filename):
    """修改文件内容, 类似sed, 传入参数为平行数组"""
    with open(filename, 'r') as f:
        rows = f.readlines()
        for old_str, new_str in zip(old_str_list, new_str_list):
            rows = map(lambda r: r.replace(old_str, new_str), rows)

    with open(filename, 'w') as f:
        for r in rows:
            f.write(r)


def csv_write(f, rows, keys, titles=None):
    writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)

    def gen_csv_writable_rows():
        if titles:
            yield titles

        for row in rows:
            it = (row.get(key, "") for key in keys)
            it = map(lambda x: "" if x is None else x, it)
            yield it

    writer.writerows(gen_csv_writable_rows())


def csv2xlsx(csv_files, names):
    """将csv格式的file列表按顺序转化为一个excel文件.

    @param<csv_files>: csv格式的文件列表，每一项是一个file object
    @param<names>    : 对应的sheet的名字列表(应与csv_files一一对应)，
                       每一项是一个str
    @return          : 转换后的execl文件的内容，bytes类型
    """

    assert len(csv_files) == len(names)

    wb = Workbook()

    for index, (csv_file, name) in enumerate(zip(csv_files, names)):
        if index == 0:
            ws = wb.active
            ws.title = name
        else:
            ws = wb.create_sheet(name)

        reader = csv.reader(csv_file, quoting=csv.QUOTE_NONNUMERIC)
        for row in reader:
            ws.append(row)

    out_f = BytesIO()
    wb.save(out_f)
    return out_f.getvalue()


def send_email(smtp_host, smtp_user, smtp_passwd,
               from_, to, subject, text=None, attachments=[], smtp_port=0):

    msg = EmailMessage()
    msg['From'] = from_
    msg['To'] = to
    msg['Subject'] = subject

    if text:
        msg.set_content(text)

    for content, mimetype, filename in attachments:
        maintype, subtype = mimetype.split('/', 1)
        msg.add_attachment(content, maintype=maintype,
                           subtype=subtype, filename=filename)

    with smtplib.SMTP_SSL(host=smtp_host, port=smtp_port) as s:
        s.login(smtp_user, smtp_passwd)
        s.send_message(msg)


def send_sys_email(to, subject,
                   from_=config.SYS_EMAIL_FROM,
                   text=None, attachments=[]):

    send_email(config.SYS_EMAIL_SMTP_HOST,
               config.SYS_EMAIL_SMTP_USER,
               config.SYS_EMAIL_SMTP_PASSWD,
               from_,
               to,
               subject,
               text=text,
               attachments=attachments,
               smtp_port=config.SYS_EMAIL_SMTP_PORT)
