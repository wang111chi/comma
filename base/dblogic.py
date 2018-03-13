#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import operator
import hashlib
from itertools import chain
from itertools import groupby
import urllib
import json
import datetime
from base64 import b64decode
import ipaddress
import time
import string
import random

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA
import sqlalchemy
from sqlalchemy.sql import select, desc, func
from sqlalchemy import and_, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert

# from base.framework import transaction, lock_str
from base import constant as const
from base import util
import config
from base import logger
from base.db import \
    cm_stock, cm_stock_log, cm_stock_batch, cm_stock_loss_log


    


def refund_settle_product(db, present_date, now, log):
    refund_settle = db.execute(select([
        t_trans_list.c.spid,
        t_trans_list.c.cur_type,
        t_trans_list.c.product_type,
        t_trans_list.c.bank_type,
        t_refund_list.c.mode,
        t_refund_list.c.amount,
        t_refund_list.c.fee,
        t_refund_list.c.id,
        t_trans_list.c.id.label('trans_id')
    ]).select_from(
        t_refund_list.join(
            t_trans_list,
            t_trans_list.c.id == t_refund_list.c.trans_id)
    ).where(and_(
        t_trans_list.c.product_type != const.PRODUCT_TYPE.PROMOTION,
        t_refund_list.c.settle_time.is_(None),
        t_refund_list.c.status == const.REFUND_STATUS.SUCCESS,
        t_refund_list.c.channel.in_((const.CHANNEL.API,
                                     const.CHANNEL.SP_SYSTEM)),
        func.date(t_refund_list.c.bank_settle_time) == present_date,
    ))).fetchall()

    if not refund_settle:
        log.info("[no refund list to settle]: present_date=<{}>"
                 .format(present_date)
        )
        return [], []

    refund_ids = [trans['id'] for trans in refund_settle]
    settle_ids = settle_product_insert(
        db, refund_settle, now, present_date, const.SETTLE_MODE.REFUND)
    return refund_ids, settle_ids


def check_product_sp(db, bank_type, product_type, spid):
    sel = select([
        text("product.status as bank_status, "
             "product.interface_mask as bank_mask, "
             "sp_product.status as sp_status, "
             "sp_product.fee_percent as sp_fee_percent, "
             "sp_product.bank_fee_percent as bank_fee_percent, "
             "sp_product.interface_mask as sp_mask")
    ]).select_from(t_product.join(
        t_sp_product,
        t_product.c.id == t_sp_product.c.product_id)
    ).where(and_(
        t_product.c.bank_type == bank_type,
        t_product.c.product_type == product_type,
        t_sp_product.c.spid == spid))

    product = db.execute(sel).first()

    if product is None:
        return False, None, {'error_code': const.API_ERROR.NO_PRODUCT}

    if const.PRODUCT_STATUS.FORBID in {product['bank_status'],
                                       product['sp_status']}:
        return False, None, {'error_code': const.API_ERROR.PRODUCT_FORBID}

    mask = product['bank_mask'] | product['sp_mask']
    bank_fee_percent = json.loads(product['bank_fee_percent'])
    fee_percent = json.loads(product['sp_fee_percent'])
    return True, mask, {'bank_fee': bank_fee_percent, 'fee': fee_percent}


@compiles(Insert)
def append_string(insert, compiler, **kw):
    s = compiler.visit_insert(insert, **kw)
    if 'append_string' in insert.kwargs:
        return s + " " + insert.kwargs['append_string']
    return s


def get_sp_pubkey(db, spid):
    """从mysql获取商户公钥"""
    return db.execute(select(
        [t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == spid)).first()['rsa_pub_key']


def _do_something(duration=2):
    import time
    time.sleep(duration)
