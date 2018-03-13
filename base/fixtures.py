#!/usr/bin/env python
# -*- coding: utf-8 -*-

# common fixtures for testing

import datetime

import pytest

from base.db import engine, meta
from base.db import t_sp_balance
from base.db import t_sp_bank_account
from base.db import t_sp_bank
from base import constant as const


__all__ = [
    'app',
    'client',
    'db',
    'hold_db',
    'f_spid',
    'f_bank_type',
    'f_now',
    'f_bank_spid',
    'f_terminal_id',
    'f_t_sp_balance',
    'f_t_sp_bank',
    'f_t_sp_bank_account',
]


@pytest.fixture()
def app():
    import wsgi_handler

    wsgi_handler.app.config["TESTING"] = True
    return wsgi_handler.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def hold_db():
    return engine.connect()


@pytest.fixture()
def db():
    conn = engine.connect()
    yield conn
    for table in reversed(meta.sorted_tables):
        conn.execute(table.delete())


@pytest.fixture()
def f_spid():
    return '1' * 10


@pytest.fixture()
def f_bank_type():
    return const.BANK_TYPE.GDB


@pytest.fixture()
def f_now():
    return datetime.datetime.now()


@pytest.fixture()
def f_bank_spid():
    return '01' * 5


@pytest.fixture()
def f_terminal_id():
    return '0' * 8


@pytest.fixture()
def f_t_sp_balance(db, f_spid):
    now = datetime.datetime.now()

    sp_balance_data = {
        'spid': f_spid,
        'balance': 0,
        'freezing': 0,
        'modify_time': now,
        'create_time': now,
    }

    for data in (dict(sp_balance_data, account_class=const.ACCOUNT_CLASS.B),
                 dict(sp_balance_data, account_class=const.ACCOUNT_CLASS.C)):
        db.execute(t_sp_balance.insert(), data)


@pytest.fixture()
def f_t_sp_bank(db, f_spid, f_bank_type, f_bank_spid, f_terminal_id):
    now = datetime.datetime.now()
    db.execute(t_sp_bank.insert(), {
        "spid": f_spid,
        "bank_type": f_bank_type,
        "bank_spid": f_bank_spid,
        "terminal_id": f_terminal_id,
        "create_time": now,
        "modify_time": now,
    })


@pytest.fixture()
def f_t_sp_bank_account(db, f_spid):
    now = datetime.datetime.now()
    sp_bank_account_data = {
        'spid': f_spid,
        'acct_name': '张三',
        'bank_name': '中国银行',
        'acct_no': '1234567890123456',
        'acct_city': '广州',
        'status': const.SP_BANK_ACCOUNT_STATUS.ACTIVE,
        'create_time': now,
        'modify_time': now,
    }
    db.execute(t_sp_bank_account.insert(), sp_bank_account_data)
