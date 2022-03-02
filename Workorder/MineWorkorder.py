import datetime, time
import json
import os
import re
import traceback

import pymysql
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from flask_login import current_user

from app import login_required
from config import Config
from useddb.models import db, Dbs, InceptionRecords
from . import MineWorkorders


@MineWorkorders.route('/MineWorkorder', methods=['GET', 'POST'])
@login_required
def MineWorkorder():
    # 定义路径
    g.path = current_app.config['INCEPTION_PATH']
    # 对输入的SQL进行是否符合SQL标准的判断
    if request.method == 'POST':
        sqltext = request.form.get('sqltext')
        type_id = request.form.get('type_id')

        error = None
        # 下面是为了规范SQL，在goinception前做的预判定
        if not str(sqltext).replace('\r\n', '').replace('\n', '').strip().endswith(';'):
            error = "SQL请以英文模式下的;结尾"
            flash(error)
        # 根据输入的分号将多条语句分割为单独的行
        sqllist = sqltext.replace('\r\n', ' ').replace('\n', ' ').replace(';', ';-*-*-*-').split('-*-*-*-')
        dbnamelist = []
        alldb_tmp = db.session.query(Dbs.name).all()
        alldbs = []
        for onedb in alldb_tmp:
            alldbs.append(onedb)
        # 提取数据库名称，并与现有的数据库名称对比，判断语句是否合法
        for sql in sqllist:
            tmp_sql = str(sql).replace('`', '').lstrip()
            if str.lower(tmp_sql).startswith('insert'):
                db_tbname = re.findall(r"insert *into *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('update'):
                db_tbname = re.findall(r"update *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('delete'):
                db_tbname = re.findall(r"delete *from *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('alter'):
                db_tbname = re.findall(r"alter *table *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('drop'):
                db_tbname = re.findall(r"drop *table *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('truncate'):
                db_tbname = re.findall(r"truncate *table *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('create'):
                db_tbname = re.findall(r"create *table *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('select'):
                error = '不支持SELECT，请修改！'

            else:
                if tmp_sql != '':
                    error = '请输入合法的SQL语句！'

        flash(error)

        # 创建SQL文件
        # 获取当前时间戳（毫秒）
        current_time = int(round(time.time() * 1000))
        current_day = time.strftime("%Y%m%d", time.localtime(time.time()))
        # 创建sql文件目录
        if not os.path.exists(g.path):
            try:
                os.mkdir(g.path)
            except Exception as e:
                error = str(e)
                flash(error)
        # 创建当天的目录
        if not os.path.exists('{path}/{current_day}'.format(path=g.path, current_day=current_day)):
            try:
                os.mkdir('{path}/{current_day}'.format(path=g.path, current_day=current_day))
            except Exception as e:
                error = str(e)
                flash(error)
        try:
            uid = g.user.id
            file_path = '{path}/{current_day}/$_{uid}_{time}_$.sql'.format(path=g.path, uid=uid, time=current_time,
                                                                            current_day=current_day)
            wfile = open('file_path', 'a+')
            # 将用户输入循环写入文件保存，以便后续分析和使用
            for sql in sqllist:
                if sql.strip() != '':
                    wfile.write(sql + '\n')
            # 写入数据库信息
            for dbname in dbnamelist:
                if dbname.strip() != '':
                    wfile.write(dbname + ' ')
            wfile.close()
            time.sleep(0.1)

            # 取文件名
            filename = os.path.basename(file_path)
        except Exception as e:
            error = str(e)
            flash(error)

        # 接下来是连接goinception来进行SQL语法判定
        conn_goinception = pymysql.connect(
            host=Config.INCEPTION_HOST,
            port=int(Config.INCEPTION_PORT),
            user=Config.INCEPTION_USER,
            password=Config.INCEPTION_PASSWORD
        )

        display_result_dict = {}
        # 初始化inception数据库的游标
        cur = conn_goinception.cursor()
        # inception参数
        prefix_format_check = ''
        # 结束语法
        suffix_format = "\ninception_magic_commit;"

        display_result = []
        successfulstatus = 'no'
        successfulnum = 0

        # 开始，获取连接信息
        prefix_format_check = "/*--user={};--password={};--host={};--port={};--enable-check;*/ " \
                                  .format(Config.MYSQLUSER, Config.MYSQLPASSWORD,
                                          Config.IP, int(Config.PORT)) + '\n' \
                              + "inception_magic_start;\n"

        # 拼接语法
        nowsql = sqltext.replace('\r\n', ' ').replace('\n', ' ')
        checksql = prefix_format_check + nowsql + suffix_format
        cur.execute(checksql)

        # 计算有多少句SQL
        count = sqltext.count(';')

        # 获取check结果
        sqlresults = cur.fetchall()
        print(sqlresults)
        for sqlresult in sqlresults:
            # 获取本次检查成功的SQL语句数量
            if sqlresult[2] == 0:
                successfulnum = successfulnum + 1
        if count == successfulnum:
            successfulstatus = 'yes'

        print(count)


    return render_template('workorder/MineWorkorder/MineWorkorder.html')
