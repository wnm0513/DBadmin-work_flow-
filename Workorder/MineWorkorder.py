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
from useddb.models import db, Dbs, InceptionRecords, Workorder, User, WorkFlow
from . import MineWorkorders

path = Config.INCEPTION_PATH


def goinceptionCheck(sqltext):
    # 接下来是连接goinception来进行SQL语法判定
    conn_goinception = pymysql.connect(
        host=Config.INCEPTION_HOST,
        port=int(Config.INCEPTION_PORT),
        user=Config.INCEPTION_USER,
        password=Config.INCEPTION_PASSWORD
    )

    # 初始化inception数据库的游标
    cur = conn_goinception.cursor()
    # inception参数
    prefix_format_check = ''
    # 结束语法
    suffix_format = "\ninception_magic_commit;"

    # 开始，获取连接信息
    prefix_format_check = "/*--user={};--password={};--host={};--port={};--enable-check;*/ " \
                              .format(Config.MYSQLUSER, Config.MYSQLPASSWORD,
                                      Config.IP, int(Config.PORT)) + '\n' \
                          + "inception_magic_start;\n"

    # 拼接语法
    nowsql = sqltext.replace('\r\n', ' ').replace('\n', ' ')
    checksql = prefix_format_check + nowsql + suffix_format
    cur.execute(checksql)

    # 获取check结果
    sqlresults = cur.fetchall()

    return sqlresults


def goinceptionExecute(sqltext):
    # 接下来是连接goinception来进行SQL语法判定
    conn_goinception = pymysql.connect(
        host=Config.INCEPTION_HOST,
        port=int(Config.INCEPTION_PORT),
        user=Config.INCEPTION_USER,
        password=Config.INCEPTION_PASSWORD
    )

    # 初始化inception数据库的游标
    cur = conn_goinception.cursor()
    # inception参数
    prefix_format_check = ''
    # 结束语法
    suffix_format = "\ninception_magic_commit;"

    # 开始，获取连接信息
    prefix_format_check = "/*--user={};--password={};--host={};--port={};--execute=1;--backup=1;*/ " \
                              .format(Config.MYSQLUSER, Config.MYSQLPASSWORD,
                                      Config.IP, int(Config.PORT)) + '\n' \
                          + "inception_magic_start;\n"

    # 拼接语法
    nowsql = sqltext.replace('\r\n', ' ').replace('\n', ' ')
    checksql = prefix_format_check + nowsql + suffix_format
    cur.execute(checksql)

    # 获取check结果
    sqlresults = cur.fetchall()

    return sqlresults


@MineWorkorders.route('/MineWorkorder', methods=['GET', 'POST'])
@login_required
def MineWorkorder():
    # 定义全局变量
    global filename, newrecordsjson
    global path

    # 定义要传给下个视图的列表
    newrecordsinfo = []
    # 对输入的SQL进行是否符合SQL标准的判断
    if request.method == 'POST':
        sqltext = request.form.get('sqltext')
        type_id = request.form.get('type_id')

        error = None
        # 下面是为了规范SQL，在goinception前做的预判定
        if not str(sqltext).replace('\r\n', '').replace('\n', '').strip().endswith(';'):
            error = "SQL请以英文模式下的';'结尾"
            flash(error)
            return render_template('workorder/MineWorkorder/MineWorkorder.html')

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
                    flash(error)
                    return render_template('workorder/MineWorkorder/MineWorkorder.html')

                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('update'):
                db_tbname = re.findall(r"update *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                    flash(error)
                    return render_template('workorder/MineWorkorder/MineWorkorder.html')

                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('delete'):
                db_tbname = re.findall(r"delete *from *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                    flash(error)
                    return render_template('workorder/MineWorkorder/MineWorkorder.html')

                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('alter'):
                db_tbname = re.findall(r"alter *table *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                    flash(error)
                    return render_template('workorder/MineWorkorder/MineWorkorder.html')

                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('drop'):
                db_tbname = re.findall(r"drop *table *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                    flash(error)
                    return render_template('workorder/MineWorkorder/MineWorkorder.html')

                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('truncate'):
                db_tbname = re.findall(r"truncate *table *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                    flash(error)
                    return render_template('workorder/MineWorkorder/MineWorkorder.html')

                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('create'):
                db_tbname = re.findall(r"create *table *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]
                if dbname == '':
                    error = '请指定数据库'
                    flash(error)
                    return render_template('workorder/MineWorkorder/MineWorkorder.html')

                dbnamelist.append(dbname)

            elif str.lower(tmp_sql).startswith('select'):
                error = '不支持SELECT，请修改！'
                flash(error)
                return render_template('workorder/MineWorkorder/MineWorkorder.html')

            else:
                if tmp_sql != '':
                    error = '请输入合法的SQL语句！'
                    flash(error)
                    return render_template('workorder/MineWorkorder/MineWorkorder.html')

        # 创建SQL文件
        # 获取当前时间戳（毫秒）
        current_time = int(round(time.time() * 1000))
        current_day = time.strftime("%Y%m%d", time.localtime(time.time()))
        # 创建sql文件目录
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except Exception as e:
                error = str(e)
                flash(error)
                return render_template('workorder/MineWorkorder/MineWorkorder.html')

        # 创建当天的目录
        if not os.path.exists('{path}/{current_day}'.format(path=path, current_day=current_day)):
            try:
                os.mkdir('{path}/{current_day}'.format(path=path, current_day=current_day))
            except Exception as e:
                print(e)
                error = str(e)
                flash(error)
                return render_template('workorder/MineWorkorder/MineWorkorder.html')

        try:
            uid = g.user.id
            file_path = '{path}/{current_day}/$_{uid}_{time}_$.sql'.format(path=path, uid=uid, time=current_time,
                                                                           current_day=current_day)
            wfile = open('{file_path}'.format(file_path=file_path), 'a+')
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
            print(e)
            error = str(e)
            flash(error)
            return render_template('workorder/MineWorkorder/MineWorkorder.html')

        # 调用goinceptioncheck获取check结果
        sqlresults = goinceptionCheck(sqltext)

        # 计算有多少句SQL
        count = sqltext.count(';')

        for sqlresult in sqlresults:

            # 获取本次检查成功的SQL语句数量
            if sqlresult[2] == 0:
                success_status = 1
            else:
                success_status = 0

            execute_status = 0
            goinception_record = InceptionRecords(uid=g.user.id, sqltext=sqlresult[5], filename=filename, sqlnums=count,
                                                  success_status=success_status,
                                                  applydate=current_day, applytime=datetime.datetime.now(),
                                                  lastupdatetime=datetime.datetime.now(),
                                                  execute_status=execute_status)

            try:
                db.session.add(goinception_record)
                db.session.commit()
            except Exception as e:
                error = str(e)
                flash(error)

            newrecordinfo = {
                'type_id': type_id,
                'current_time': current_time,
                'current_day': current_day,
                'filename': filename
            }
            newrecordsinfo.append(newrecordinfo)
        newrecordsjson = json.dumps(newrecordsinfo)

        return redirect(url_for('MineWorkorder.OrderCheck', newrecordsjson=newrecordsjson))

    return render_template('workorder/MineWorkorder/MineWorkorder.html')


@MineWorkorders.route('/OrderCheck/<newrecordsjson>', methods=['GET', 'POST'])
@login_required
def OrderCheck(newrecordsjson):
    # 引用path
    global path
    # 定义存储check信息的列表
    checksqlsinfo = []
    # 定义存储executed信息的列表
    executedsqlsinfo = []

    # 从上个视图取值
    newrecords = json.loads(newrecordsjson)
    type_id = newrecords[0]['type_id']
    current_day = newrecords[0]['current_day']
    filename = newrecords[0]['filename']

    # 读取文件
    filecontent = open('{path}/{day}/{filename}'.format(path=path, day=current_day, filename=filename),
                       'r')
    allsqls = filecontent.readlines()
    # 将最后一行的dbname取出来
    dbnamelist = allsqls.pop().split()
    filecontent.close()

    for allsql in allsqls:

        sqlresults = goinceptionCheck(allsql)

        for sqlresult in sqlresults:
            # 整合check结果
            checksqlinfo = {
                'stage': sqlresult[1],
                'error_level': sqlresult[2],
                'stage_status': sqlresult[3],
                'error_message': sqlresult[4],
                'sql': sqlresult[5],
                'affected_rows': sqlresult[6],
                'execute_time': sqlresult[9],
                'backup_time': sqlresult[11]
            }
            checksqlsinfo.append(checksqlinfo)

    # 当别的视图请求时
    if request.method == 'GET':

        return render_template('workorder/MineWorkorder/OrderCheck.html', checksqlsinfo=checksqlsinfo, type_id=type_id)

    # 当提交表单时
    if request.method == 'POST':

        user = User.query.filter_by(id=g.user.id).first()

        # 将数据写入工单表
        workorder = Workorder(uid=user.id, deptid=user.deptId, username=user.name,
                              filename=filename, stime=datetime.datetime.now(),
                              etime=datetime.datetime.now(), applyreason=type_id,
                              status=0)

        try:
            db.session.add(workorder)
            db.session.commit()
        except Exception as e:
            error = str(e)
            flash(error)

        workorder_tmp = Workorder.query.filter_by(filename=filename).first()

        # 将数据写入审批流表
        workflow = WorkFlow(woid=workorder_tmp.id, uid=user.id, uname=user.name,
                            otime=datetime.datetime.now(), auditing=0, nowstep=1,
                            maxstep=3)

        try:
            db.session.add(workflow)
            db.session.commit()
        except Exception as e:
            error = str(e)
            flash(error)

        return redirect(url_for('OrderProcess.OrderProcess'))