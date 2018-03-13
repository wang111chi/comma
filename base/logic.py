#!/usr/bin/env python3

from functools import wraps, reduce

import requests
from flask import session, url_for, request
import ipaddress
import datetime

from base import logger
from base import constant as const
from base import pp_interface as pi
from base.framework import Redirect, TempResponse
from base.framework import SpAdminJsonErrorResponse, SpAdminTempErrorResponse
from base.db import t_sp_admins, engine
from base import dblogic as dbl


def callback_url(callback_id,
                 mode,
                 url,
                 method=const.HTTP_METHOD.GET,
                 body=None,
                 logger=logger.get("cgi-log")):
    u"""回调URL.

    @param<callback_id>: 回调在数据库中的ID(对应的表为callback_url)
    @param<mode>: 回调模式，详见const.CALLBACK_URL.MODE
    @param<url>: 回调的URL
    @param<method>: 回调的HTTP方法
    @param<body>: 如果回调方法为POST， 则为需要POST的HTTP body
    @param<logger>: 用于记日志的对象

    @return: (is_sucess,   # 回调是否成功
              resp_code,   # 回调的HTTP响应状态码
              resp_body,   # 回调的HTTP响应body
             )
    """
    http_method = requests.get

    if method == const.HTTP_METHOD.POST:
        http_method = requests.post

    # resp_code = None
    # resp_body = None

    try:
        if body is None:
            r = http_method(url)
        else:
            r = http_method(url, body)
    except Exception:
        logger.error("[callback request error]: "
                     "<callback_id>=><%s>, <url>=><%s>",
                     callback_id, url, exc_info=True)
        is_success = False
    else:
        # resp_code = r.status_code
        # resp_body = r.content
        is_success = callback_url_resp_check(r, mode, callback_id, url, logger)

    return is_success


def callback_url_resp_check(resp, mode, callback_id, url, logger):
    u"""回调URL的结果检查，根据响应确定回调是否成功.

    @param resp: requests的响应,
                 http://docs.python-requests.org/en/master/api/#requests.Response # noqa
    @param mode: 回调URL的模式，详见const.CALLBACK_URL.MODE
    """
    if resp.status_code != 200:
        logger.error("[callback request error]: "
                     "<callback_id>=><%s>, <url>=><%s>, <resp_code>=><%s>",
                     callback_id, url, resp.status_code, exc_info=True)
        return False

    # TODO: judge according to mode
    try:
        json_resp = resp.json()
    except ValueError:
        logger.error("[callback request error]: "
                     "<callback_id>=><%s>, <url>=><%s>",
                     callback_id, url, exc_info=True)

        return False

    if json_resp.get('retcode') == 0:
        return True

    return False


SP_ADMIN_MENUS = [
    {"type": "menu", "title": "账户概览", "url": "/", "role": (
        const.SP_ADMIN.ROLE.SP_ALL +
        const.SP_ADMIN.ROLE.FENLE_ALL
    )},
    {"type": "group", "title": "创建交易", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
    )},
    {"type": "menu", "title": "分期交易", "url": "/trans/layaway", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
    )},
    {"type": "menu", "title": "纯积分", "url": "/trans/point", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
    )},
    {"type": "menu", "title": "积分+现金", "url": "/trans/point_cash", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
    )},
    {"type": "menu", "title": "无卡订购", "url": "/trans/consume", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
    )},
    {"type": "menu", "title": "积分查询", "url": "/point/load", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
    )},
    {"type": "group", "title": "交易管理", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "menu", "title": "交易订单", "url": "/trans/list", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "menu", "title": "退款查询", "url": "/refund/list", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.CASHIER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "group", "title": "结算管理", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "menu", "title": "已结算金额", "url": "/settle/list", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "group", "title": "对账单", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "menu", "title": "交易账单", "url": "/statement", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "group", "title": "资金", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "menu", "title": "资金概况", "url": "/fund/unsettled", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "menu", "title": "提现记录查询", "url": "/fund/withdraw", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "menu", "title": "资金流水", "url": "/fund/history", "role": (
        const.SP_ADMIN.ROLE.SUPER,
        const.SP_ADMIN.ROLE.ACCOUNTANT,
    )},
    {"type": "group", "title": "资金提现", "role": (
        const.SP_ADMIN.ROLE.FENLE_SUPER,
    )},
    {"type": "menu", "title": "待提现商户", "url": "/admin/withdraw/list",
     "role": (const.SP_ADMIN.ROLE.FENLE_SUPER, )
    },
    {"type": "menu", "title": "提现历史", "url": "/admin/withdraw/history",
     "role": (const.SP_ADMIN.ROLE.FENLE_SUPER, )
    },
    {"type": "group", "title": "交易统计", "role": (
        const.SP_ADMIN.ROLE.FENLE_SUPER,
    )},
    {"type": "menu", "title": "交易错误统计", "url": "/admin/count/trans",
     "role": (const.SP_ADMIN.ROLE.FENLE_SUPER, )
    },
]


SP_ADMIN_CONFIG_MENUS = [
    {"type": "group",
     "title": "账户设置",
     "role": (
         const.SP_ADMIN.ROLE.SP_ALL +
         const.SP_ADMIN.ROLE.FENLE_ALL)
    },
    {"type": "menu",
     "title": "修改密码",
     "url": "/admin/password/reset",
     "role": (
         const.SP_ADMIN.ROLE.SP_ALL +
         const.SP_ADMIN.ROLE.FENLE_ALL)
    },
]


def sp_admin_required(roles=[]):
    """检查商户管理员的登录状态."""

    def deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            error_handler = SpAdminJsonErrorResponse if request.is_xhr \
                else SpAdminTempErrorResponse

            # make sure db_conn is provided before sp_admin_required
            db = kwargs["db"]

            admin_id = session.get(const.SESSION.KEY_ADMIN_ID)
            if admin_id is None:
                return Redirect(url_for("admin.login_load"))

            admin = db.execute(t_sp_admins.select().where(
                t_sp_admins.c.id == admin_id
            ).where(
                t_sp_admins.c.status == const.SP_ADMIN.STATUS.NORMAL
            )).first()
            if admin is None:
                session.clear()
                return Redirect(url_for("admin.login_load"))

            to_update = {"last_login_time": datetime.datetime.now()}

            try:
                ip = ipaddress.IPv4Address(request.remote_addr)
            except ipaddress.AddressValueError:
                pass
            else:
                to_update["last_login_ip"] = int(ip)

            # 记录时间和ip
            db.execute(t_sp_admins.update().where(
                t_sp_admins.c.id == admin_id).values(to_update))

            # 检查权限配置是否非法
            if not admin["role"]:
                return error_handler("没有权限")

            channel = None
            if admin["role"] in const.SP_ADMIN.ROLE.SP_ALL:
                channel = "sp"
            elif admin["role"] in const.SP_ADMIN.ROLE.FENLE_ALL:
                channel = "fenle"
            if not channel:
                return error_handler("权限错误")

            nonlocal roles
            if roles is not None:
                if not isinstance(roles, (list, tuple)):
                    roles = (roles, )
                if admin["role"] not in roles:
                    return error_handler("没有权限")

            kwargs["channel"] = channel
            kwargs["admin_id"] = admin_id
            kwargs["role"] = admin["role"]
            kwargs["spid"] = admin["spid"]
            resp = old_handler(*args, **kwargs)

            if isinstance(resp, TempResponse):
                if channel == "sp":
                    sp_name = dbl.get_sp_info(db, admin["spid"])["sp_name"]
                    resp.context_update(sp_name=sp_name)
                elif channel == "fenle":
                    sp_name = admin["name"]
                    resp.context_update(sp_name=sp_name)

                # 添加自定义变量
                resp.context_update(
                    menus=_gen_menus(
                        SP_ADMIN_MENUS, admin["role"]),
                    config_menus=_gen_menus(
                        SP_ADMIN_CONFIG_MENUS, admin["role"]),
                )

            return resp

        return new_handler

    return deco


def _gen_menus(candidates, role):
    menus = []
    for item in candidates:
        if role not in item["role"]:
            continue
        display_item = dict(item)
        display_item.pop("role", None)
        display_item["active"] = request.path == item.get("url")
        menus.append(display_item)
    return menus
