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
from sqlalchemy import and_

from login_required import login_required
from config import Config
from useddb.models import db, Dbs, InceptionRecords, Workorder, User, DbsDept, Departments
from . import MineWorkorders, send_dingding, send_mail

path = Config.INCEPTION_PATH


def goinceptionCheck(dbname, sqltext):
    # 根据数据库来查ip
    host_IP = Dbs.query.filter(Dbs.name == dbname).first()
    if host_IP is None:
        error = "库不存在"
        return error

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
                                      host_IP.ip, int(Config.PORT)) + '\n' \
                          + "inception_magic_start;\n"

    # 拼接语法
    nowsql = sqltext.replace('\r\n', ' ').replace('\n', ' ')
    checksql = prefix_format_check + nowsql + suffix_format
    cur.execute(checksql)

    # 获取check结果
    sqlresults = cur.fetchall()

    cur.close()
    conn_goinception.close()

    return sqlresults


def goinceptionExecute(dbname, sqltext):
    # 根据数据库来查ip
    host_IP = Dbs.query.filter(Dbs.name == dbname).first()

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
                                      host_IP.ip, int(Config.PORT)) + '\n' \
                          + "inception_magic_start;\n"

    # 拼接语法
    nowsql = sqltext.replace('\r\n', ' ').replace('\n', ' ')
    checksql = prefix_format_check + nowsql + suffix_format
    cur.execute(checksql)

    # 获取check结果
    sqlresults = cur.fetchall()

    cur.close()
    conn_goinception.close()

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

        # 必须选择上线类型
        if type_id == '--请选择类型--':
            error = "请选择相应的上线类型"
            flash(error)
            return render_template('workorder/MineWorkorder/MineWorkorder.html')
        # 下面是为了规范SQL，在goinception前做的预判定
        if not str(sqltext).replace('\r\n', '').replace('\n', '').strip().endswith(';'):
            error = "以英文模式下的';'结尾"
            flash(error)
            return render_template('workorder/MineWorkorder/MineWorkorder.html')

        # 根据输入的分号将多条语句分割为单独的行
        sqllist = sqltext.replace('\r\n', ' ').replace('\n', ' ').replace(';', ';-*-*-*-').split('-*-*-*-')
        dbnamelist = []

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

            # 在用户不是管理员的情况下
            if not g.user.is_super():
                # 对用户是否有权限操作数据库进行判断
                mydept_dbs = []  # 部门维度的数据库权限列表
                # 这里是对部门的权限进行判断，如果部门拥有这个数据库，那么就可以操作这个数据库，否则报错提示没有权限
                mydept_db = db.session.query(Dbs.name) \
                    .join(DbsDept, DbsDept.dbid == Dbs.id) \
                    .join(Departments, Departments.id == DbsDept.deptid) \
                    .join(User, User.deptId == Departments.id) \
                    .filter(User.id == g.user.id).all()
                for onedb in mydept_db:
                    mydept_dbs.append(onedb[0])

                nopridblist = list(set(dbnamelist).difference(set(mydept_dbs)))
                # 如果含有没有操作权限的数据库
                if len(nopridblist) > 0:
                    error = '您不具有以下数据库的操作权限：{nopridblist}'.format(nopridblist=nopridblist)
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
            file_path = '{path}/{current_day}/$_{uid}_{daytime}_$.sql'.format(path=path, uid=uid,
                                                                              daytime=current_day + str(current_time),
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

        # 计算有多少句SQL
        count = sqltext.count(';')

        # 读取文件
        filecontent = open('{path}/{day}/{filename}'.format(path=path, day=current_day, filename=filename),
                           'r')
        allsqls = filecontent.readlines()
        # 将最后一行的dbname取出来
        dbnamelist = allsqls.pop().split()
        filecontent.close()

        for num in range(len(dbnamelist)):

            # 调用goinceptioncheck获取check结果
            sqlresults = goinceptionCheck(dbnamelist[num], allsqls[num])
            if sqlresults == '库不存在':
                flash('[ {nodbname} ]'.format(nodbname=dbnamelist[num]) + sqlresults)
                return render_template('workorder/MineWorkorder/MineWorkorder.html')

            for sqlresult in sqlresults:

                # 获取本次检查成功的SQL语句数量
                if sqlresult[2] == 0:
                    success_status = 1
                else:
                    success_status = 0

                goinception_record = InceptionRecords(uid=g.user.id, sqltext=sqlresult[5], filename=filename,
                                                      sqlnums=count,
                                                      success_status=success_status,
                                                      applydate=current_day, applytime=datetime.datetime.now(),
                                                      )

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
    is_error = None
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

    for num in range(len(dbnamelist)):

        sqlresults = goinceptionCheck(dbnamelist[num], allsqls[num])

        for sqlresult in sqlresults:

            if sqlresult[4] == None:
                is_error = 0
            else:
                is_error = 1

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
        return render_template('workorder/MineWorkorder/OrderCheck.html', checksqlsinfo=checksqlsinfo, type_id=type_id,
                               filename=filename, is_error=is_error)

    # 当提交表单时
    if request.method == 'POST':

        user = User.query.filter_by(id=g.user.id).first()

        current_time = int(round(time.time() * 10))

        woid = int(str(current_day) + str(current_time))

        # 将数据写入工单表
        workorder = Workorder(id=woid, uid=user.id, deptid=user.deptId, username=user.name,
                              filename=filename, stime=datetime.datetime.now(),
                              etime=datetime.datetime.now(), applyreason=type_id,
                              status=0, process_status=1, process_otime=datetime.datetime.now())

        try:
            db.session.add(workorder)
            db.session.commit()
        except Exception as e:
            error = str(e)
            flash(error)

        workorder_tmp = Workorder.query.filter_by(filename=filename).first()

# 这里想直接取消审批流表，再工单表中添加一个字段process_status，1为提交、2为经理审批通过、3是DBA审批通过、4经理驳回、5为DBA驳回

       # # 将数据写入审批流表
       # workflow = WorkFlow(woid=workorder_tmp.id, uid=user.id, uname=user.name,
       #                     otime=datetime.datetime.now(), auditing=0, nowstep=1,
       #                     maxstep=3)

       # try:
       #     db.session.add(workflow)
       #     db.session.commit()
       # except Exception as e:
       #     error = str(e)
       #     flash(error)

        # 消息推送给部门经理
        send_dept = Departments.query.filter_by(id=workorder.deptid).first()
        receive_dept_manager = User.query.filter(and_(User.deptId == send_dept.id, User.ismanager == 1)).first()
        send_user = User.query.filter_by(name=workorder.username).first()
        content = "您好，{confirm_user}，有新的审批待您确认：\n" \
                  "审批单号：{woid}，\n" \
                  "发起人：{user}，\n" \
                  "发起部门：{dept}，\n" \
                  "申请理由：{reason}\n\n" \
                  "请登录DBAdmin查看待审批内容！\n地址：http://{ip}" \
            .format(woid=workorder_tmp.id,
                    user=send_user.name,
                    dept=send_dept.deptname,
                    reason=workorder.applyreason,
                    confirm_user=receive_dept_manager.name,
                    ip=Config.WEB_IP
                    )
        # send_mail(content, receive_dept_manager.email)
        # send_dingding(content, receive_dept_manager.ding)

        return redirect(url_for('OrderProcess.OrderProcess'))


## 取消 ##
@MineWorkorders.route('/refused/<filename>/', methods=['GET', 'POST'])
@login_required
def cancel(filename):
    # 取出记录表中的信息
    record = InceptionRecords.query.filter_by(filename=filename).first()
    date = str(record.applydate)
    orderdate = str(date).replace('-', '')

    # 删除生成的文件
    file_path = '{path}/{current_day}/{filename}'.format(path=path, current_day=orderdate, filename=filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # 提交
    try:
        db.session.query(InceptionRecords).filter(InceptionRecords.filename == filename).delete()
        db.session.commit()
    except Exception as e:
        error = str(e)
        flash(error)

    return redirect(url_for('MineWorkorder.MineWorkorder'))
