#!/usr/bin/env python
# -*- coding: utf-8 -*-

# flake8: noqa

from enum import Enum

class BOOLEAN(object):
    FALSE = 0
    TRUE  = 1

    ALL   = (FALSE, TRUE)


class TASK:
    class IDENT(Enum):
        BASE                        = 0
        TEST                        = -1

        SETTLE                      = 1001 # 结算
        ASYN_REFUND                 = 1002 # 异步退货

        WITHDRAW                    = 2001 # 提现
        BATCH_PAY                   = 2002 # 代付
        WITHDRAW_REPORT             = 2003 # 提现报表
        QUERY_BATCH_PAY             = 2004 # 查询代付状态

        BANK_STATEMENT              = 3001 # 生成跟银行的对账单
        BANK_STATEMENT_RESULT_CHECK = 3002 # 接收检查银行返回的对账结果并进行处理
        STATEMENT_REFUND            = 3003 # 对账异常系统退货

        GENERAL_DATA_CHECK          = 9001 # 一般性数据检查脚本，各种内部对账合计


    class RUN_TYPE(Enum):
        MANUAL = 0 # 手动运行
        AUTO   = 1 # 自动运行(比如定时任务)


    class STATUS:
        RUNNING = 0 # 任务开始跑
        DONE    = 1 # 任务跑成功(没出异常，且主动设置了run_success为True)
