#!/usr/bin/env python3

import importme

import datetime

from sqlalchemy.sql import select
from sqlalchemy.sql import and_

from task import DailyTask
from base.db import t_sp_balance, t_sp_bank_account, t_withdraw
from base.db import t_batch_pay
from base.framework import transaction
from base import constant as const
from base import util
from base import batch_pay_interface as bpi
from base import dblogic as dbl
from base import logger
from base import date_util as du


class WithdrawTask(DailyTask):

    u"""申请提现."""

    IDENT = const.TASK.IDENT.WITHDRAW
    DEPENDENCIES = [
        const.TASK.IDENT.SETTLE,
    ]

    def _check(self):
        if not super(WithdrawTask, self)._check():
            return False

        # 法定节假日顺延
        if du.is_holiday():
            return False

        return True

    def _handle_balance(self, balance):
        stmt = select([
            t_sp_bank_account.c.spid,
            t_sp_bank_account.c.sp_name,
            t_sp_bank_account.c.acct_name,
            t_sp_bank_account.c.bank_name,
            t_sp_bank_account.c.acct_no,
            t_sp_bank_account.c.acct_city,
            t_sp_bank_account.c.is_public,
            t_sp_bank_account.c.union_no,
        ]).where(
            t_sp_bank_account.c.status == const.SP_BANK_ACCOUNT_STATUS.ACTIVE
        ).where(
            t_sp_bank_account.c.cur_type == const.CUR_TYPE.RMB
        ).where(
            t_sp_bank_account.c.spid == balance["spid"]
        )

        account = self.db.execute(stmt).first()

        if account is None:
            self.logger.warn(
                '[withdraw error]: sp bank account not exist, '
                'spid=><%s>', balance["spid"])
            return

        now = datetime.datetime.now()
        spid = balance["spid"]
        amount = balance["balance"] - balance["freezing"]
        # TODO 限制最小提现额度？
        with transaction(self.db) as trans:
            # 创建提现单
            withdraw_id = util.gen_withdraw_id(spid)
            self.db.execute(t_withdraw.insert(), {
                "id": withdraw_id,
                "spid": spid,
                "cur_type": const.CUR_TYPE.RMB,
                "amount": amount,
                "sp_name": account["sp_name"],
                "acct_name": account["acct_name"],
                "bank_name": account["bank_name"],
                "acct_no": account["acct_no"],
                "acct_city": account["acct_city"],
                "is_public": account["is_public"],
                "union_no": account["union_no"],
                "status": const.WITHDRAW_STATUS.INIT,
                "create_time": now,
                "modify_time": now,
            })

            # 冻结余额
            dbl.update_sp_balance(
                self.db, spid, const.ACCOUNT_CLASS.C,
                amount, const.BIZ.WITHDRAW,
                ref_str_id=withdraw_id, now=now, is_freezing=True)

            trans.finish()

    def _handle_batch_pay(self, withdraw_list):
        if len(withdraw_list) < 1:
            return

        batch_pay_id = util.gen_batch_pay_id()
        now = datetime.datetime.now()

        with transaction(self.db) as trans:
            # 创建代付单
            self.db.execute(t_batch_pay.insert(), {
                "id": batch_pay_id,
                "status": const.BATCH_PAY_STATUS.INIT,
                "create_time": now,
                "modify_time": now,
            })

            # 更新相应提现单的批次号
            self.db.execute(t_withdraw.update().where(
                t_withdraw.c.id.in_([item["id"] for item in withdraw_list])
            ).values(batch_pay_id=batch_pay_id, modify_time=now))

            trans.finish()

        for withdraw in withdraw_list:
            withdraw["is_verify"] = False

        # 调接口
        status = bpi.batch_pay(batch_pay_id, withdraw_list)
        now = datetime.datetime.now()

        with transaction(self.db) as trans:
            # 更改代付单的状态
            self.db.execute(t_batch_pay.update().where(
                t_batch_pay.c.id == batch_pay_id
            ).values(status=status, modify_time=now))

            # 更新相应提现单的状态
            self.db.execute(t_withdraw.update().where(
                t_withdraw.c.id.in_([item["id"] for item in withdraw_list])
            ).values(status=status, modify_time=now))

            if status == const.WITHDRAW_STATUS.SUBMIT_FAIL:
                # 恢复冻结余额
                for withdraw in withdraw_list:
                    dbl.update_sp_balance(self.db, withdraw["spid"],
                                          const.ACCOUNT_CLASS.C,
                                          -withdraw["amount"],
                                          const.BIZ.WITHDRAW,
                                          ref_str_id=withdraw["id"],
                                          now=now, is_freezing=True)
            trans.finish()

    def _run(self):
        # 第一步：选出待提现的余额，创建提现单

        stmt = select([
            t_sp_balance.c.spid,
            t_sp_balance.c.balance,
            t_sp_balance.c.freezing,
        ]).where(
            t_sp_balance.c.cur_type == const.CUR_TYPE.RMB
        ).where(
            t_sp_balance.c.account_class == const.ACCOUNT_CLASS.C
        ).where(
            t_sp_balance.c.balance > t_sp_balance.c.freezing
        )

        for balance in self.db.execute(stmt):
            self._handle_balance(balance)

        # 第二步：调批量代付接口
        # stmt = select([
        #     t_withdraw.c.id,
        #     t_withdraw.c.spid,
        #     t_withdraw.c.amount,
        #     t_withdraw.c.acct_name,
        #     t_withdraw.c.acct_no,
        #     t_withdraw.c.acct_city,
        #     t_withdraw.c.is_public,
        #     t_withdraw.c.union_no,
        #     t_withdraw.c.memo,
        # ]).where(
        #     t_withdraw.c.status == const.WITHDRAW_STATUS.INIT
        # ).where(
        #     t_withdraw.c.cur_type == const.CUR_TYPE.RMB
        # )

        # to_submit = list(map(dict, self.db.execute(stmt)))

        # for i in range(0, len(to_submit), 30):
        #     self._handle_batch_pay(to_submit[i:i + 30])

        self.run_success = True


if __name__ == "__main__":
    WithdrawTask.cli()
