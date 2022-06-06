import datetime

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib

from sqlalchemy import distinct
from sqlalchemy.sql.functions import count

import useddb
import pymysql
from app import login_required
from config import Config
from useddb.models import db, User, UsersRoles, Departments, Dbs, DbsDept, DbsUser, QueryHistory
from . import sqlExecutes


def mysqlexecute(select_db, sql):
    # 根据数据库来查ip
    select_IP = Dbs.query.filter(Dbs.name == select_db).first()

    # 接下来是连接mysql数据库
    conn = pymysql.connect(
        host=select_IP.ip,
        port=int(Config.PORT),
        user=Config.MYSQLUSER,
        password=Config.MYSQLPASSWORD,
        db=select_db
    )

    # 初始化游标
    cur = conn.cursor()
    # 执行语句
    cur.execute(sql)

    # 获取返回结果
    result_all = cur.fetchall()
    result = []
    for i in result_all:
        result_tmp = i
        result.append(result_tmp)
    # 获取标题
    field_names = [i[0] for i in cur.description]

    cur.close()
    conn.close()
    return field_names, result, select_IP.ip

# 判断是否为select
def isSelect(sql):
    chsql = sql.upper().strip()
    if not chsql.startswith("SELECT "):
        return False
    return True


## SQL执行 ##
@sqlExecutes.route('/sqlExecute', methods=['GET', 'POST'])
@login_required
def sqlExecute():
    # 根据用户权限选择可选择查询的数据库
    if g.user.is_super():
        dbs = db.session.query(Dbs.name).all()
    else:
        dbs = []
        mydept_dbs = db.session.query(Dbs.name) \
            .join(DbsDept, DbsDept.dbid == Dbs.id) \
            .join(Departments, Departments.id == DbsDept.deptid) \
            .join(User, User.deptId == Departments.id) \
            .filter(User.id == g.user.id).all()
        for mydept_db in mydept_dbs:
            deptdbs = db.session.query(Dbs.ip, Dbs.name).group_by(Dbs.ip).filter(Dbs.name == mydept_db[0]).first()
            mydeptdblist = {
                'name': deptdbs.name
            }
            dbs.append(mydeptdblist)

    # 如果提交了SQL语句
    if request.method == 'POST':
      #  select_env = request.form.get('select_env')
        select_db = request.form.get('select_db')
        sqltext = request.form.get('sqltext')

      #  if select_env == '--请选择环境--':
       #     error = "请选择环境！"
        #    flash(error)
         #   return render_template('SQL/Execute/sqlExecute.html', dbs=dbs)

        if select_db == '--请选择数据库--':
            error = "请选择数据库！"
            flash(error)
            return render_template('SQL/Execute/sqlExecute.html', dbs=dbs)

        if not str(sqltext).replace('\r\n', '').replace('\n', '').strip().endswith(';'):
            error = "SQL请以英文模式下的';'结尾"
            flash(error)
            return render_template('SQL/Execute/sqlExecute.html', dbs=dbs)

        tmp = isSelect(sqltext)
        if not tmp:
            error = '只支持SELECT语句！'
            flash(error)
            return render_template('SQL/Execute/sqlExecute.html', dbs=dbs)

        # 返回了三个值，【0】是表头， 【1】是内容的列表，【2】是ip
        result = mysqlexecute(select_db, sqltext)
        # 这里是为了让结果与表头对齐
        count_col = len(result[0])

        try:
            select_record = QueryHistory(uid=g.user.id, name=g.user.name, dbname=select_db,
                                         sqltext=sqltext, host=result[2],
                                         create_time=datetime.datetime.now())
            db.session.add(select_record)
            db.session.commit()

        except Exception as e:
            error = str(e)
            flash(error)

        return render_template('SQL/Execute/sqlExecute.html', result=result, dbs=dbs, count_col=count_col)

    return render_template('SQL/Execute/sqlExecute.html', dbs=dbs)
