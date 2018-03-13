import pymysql.cursors
import time
import datetime
import numpy
import pandas as pd
import sys
# import os
from shutil import copyfile
import math
import requests


print("链接数据库......")


def read_database():
    try:
        connection = pymysql.connect(
            host='rm-wz99uqudq1rk4ep9o.mysql.rds.aliyuncs.com',
            port=3306,
            user='bigdata',
            password='Comma_2018',
            db='csys',
            charset='utf8')

        cur = connection.cursor()
    except pymysql.err.OperationalError as err:
        print("Connection error: ", err)
        sys.exit(1)
    else:
        print("Pass the Database Connection.")

    print("数据读入......")

    #################################################################
    sql = '''select * from cm_order_payment_attach'''

    database_start_time = time.time()
    try:
        cur.execute(sql)
    except pymysql.err.ProgrammingError:
        print("Sql error: can not submit MySql script!")
        sys.exit(1)
    result = cur.fetchall()
    print("第一表长度：", len(result))

    return result


picture_list = read_database()


def request(name):
    url = "http://api.commaai.cn/" + name
    response = requests.get(url, stream=True)
    return response


for i in picture_list:
    #print(i[1])
    picture = request(i[3])
    break

for i in picture:
    print(picture)

