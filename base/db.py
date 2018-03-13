#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import event
from sqlalchemy import select
from sqlalchemy import exc

import config


# ############ mysql ################

meta = MetaData()

engine = create_engine(config.DATABASE_URL)
meta.reflect(bind=engine)
engine = engine.execution_options(autocommit=True)

cm_order = meta.tables['cm_order']
cm_order_goods = meta.tables['cm_order_goods']
cm_order_payment = meta.tables['cm_order_payment']
cm_order_coupon = meta.tables['cm_order_coupon']

cm_coupon_bind = meta.tables['cm_coupon_bind']

cm_stock = meta.tables['cm_stock']
cm_stock_log = meta.tables['cm_stock_log']
cm_stock_batch = meta.tables['cm_stock_batch']
cm_stock_batch_log = meta.tables['cm_stock_batch_log']
cm_stock_record = meta.tables['cm_stock_record']
cm_stock_record_batch = meta.tables['cm_stock_record_batch']
cm_stock_loss_log = meta.tables['cm_stock_loss_log']

cm_brand = meta.tables['cm_brand']
cm_goods = meta.tables['cm_goods']
cm_goods_category = meta.tables['cm_goods_category']
cm_goods_category_bind = meta.tables['cm_goods_category_bind']
cm_goods_attribute = meta.tables['cm_goods_attribute']
cm_goods_attribute_bind = meta.tables['cm_goods_attribute_bind']
cm_goods_rfid = meta.tables['cm_goods_rfid']
cm_sku = meta.tables['cm_sku']

cm_package = meta.tables['cm_package']
cm_package_goods = meta.tables['cm_package_goods']

cm_depot = meta.tables['cm_depot']
cm_store = meta.tables['cm_store']
cm_store_action_event = meta.tables['cm_store_action_event']

cm_user = meta.tables['cm_user']
cm_user_platform = meta.tables['cm_user_platform']
cm_region = meta.tables['cm_region']


@event.listens_for(engine, "engine_connect")
def ping_connection(connection, branch):
    # 解决MySQL自动断开长时间空闲的连接导致SQLAlchemy连接池中的连接失效的问题
    # 详见 http://docs.sqlalchemy.org/en/latest/core/pooling.html#pool-disconnects # noqa

    if branch:
        # "branch" refers to a sub-connection of a connection,
        # we don't want to bother pinging on these.
        return

    # turn off "close with result".  This flag is only used with
    # "connectionless" execution, otherwise will be False in any case
    save_should_close_with_result = connection.should_close_with_result
    connection.should_close_with_result = False

    try:
        # run a SELECT 1.   use a core select() so that
        # the SELECT of a scalar value without a table is
        # appropriately formatted for the backend
        connection.scalar(select([1]))
    except exc.DBAPIError as err:
        # catch SQLAlchemy's DBAPIError, which is a wrapper
        # for the DBAPI's exception.  It includes a .connection_invalidated
        # attribute which specifies if this connection is a "disconnect"
        # condition, which is based on inspection of the original exception
        # by the dialect in use.
        if err.connection_invalidated:
            # run the same SELECT again - the connection will re-validate
            # itself and establish a new connection.  The disconnect detection
            # here also causes the whole connection pool to be invalidated
            # so that all stale connections are discarded.
            connection.scalar(select([1]))
        else:
            raise
    finally:
        # restore "close with result"
        connection.should_close_with_result = save_should_close_with_result
