import datetime

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib

from sqlalchemy import distinct

import useddb
import pymysql
from app import login_required
from useddb.models import db, User, UsersRoles, Departments, Dbs, DbsDept, DbsUser
from . import sqlExecutes


## SQL执行 ##
@sqlExecutes.route('/sqlExecute', methods=['GET', 'POST'])
@login_required
def sqlExecute():
    dbs_ip = db.session.query(Dbs.ip).group_by(Dbs.ip).all()
    dbs_name = db.session.query(Dbs.name).all()
    # 如果提交了SQL语句
    if request.method == 'POST':
        allsqltext = request.form.get('allsqltext')

    return render_template('SQL/Execute/sqlExecute.html', dbs_ip=dbs_ip, dbs_name=dbs_name)
