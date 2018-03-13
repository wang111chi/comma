#!/usr/bin/env python3

import importme

import os
import sys
import datetime
import uuid

import click
from sqlalchemy.sql import select, distinct

from base.db import engine
from base.db import cm_depot, cm_sku, cm_stock


class Stock():

    def __init__(self, stock_id):
        self.stock_id = stock_id
        self._db = None
        self.depot_id = None
        self.store_id = None
        self.sku_id = None
        self.goods_id = None

    def set_stock_id(self, stock_id):
        self.__init__(stock_id)
        return self

    @property
    def whoami(self):
        return "stock_id <{}>".format(self.stock_id)

    @property
    def db(self):
        if not self._db:
            self._db = engine.connect()
        return self._db

    def analyse_stock_id(self):
        if self.depot_id is None:
            stock = self.db.execute(select([
                cm_stock.c.depot_id,
                cm_stock.c.sku_id,
            ]).where(cm_stock.c.stock_id == self.stock_id)
            ).first()

            if not stock:
                return self

            self.depot_id = stock.depot_id
            self.sku_id = stock.sku_id
        return self

    def get_store_id(self):
        if self.store_id is None:
            depot = self.db.execute(select([
                cm_depot.c.store_id,
            ]).where(cm_depot.c.depot_id == self.depot_id)
            ).first()
            if not depot:
                return self
            self.store_id = depot.store_id
        return self

    def get_goods_id(self):
        if self.goods_id is None:
            sku = self.db.execute(select([
                cm_sku.c.sku_id,
            ]).where(cm_sku.c.sku_id == self.sku_id)
            ).first()

            if not sku:
                return self
            self.goods_id = sku.goods_id
        return self
