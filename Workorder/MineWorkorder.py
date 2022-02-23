import re

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from app import login_required
from useddb.models import db, Dbs
from . import MineWorkorders


@MineWorkorders.route('/MineWorkorder', methods=['GET', 'POST'])
@login_required
def MineWorkorder():
    # 对输入的SQL进行是否符合SQL标准的判断
    if request.method == 'post':
        sqltext = request.form.get('sqltext')
        type_id = request.form.get('type_id')
        # 初步检查是否指定库名加表名
        if not str(sqltext).replace('\r\n', '').replace('\n', '').strip().endswith(';'):
            error = "请以英文模式的分号';'结尾"
            flash(error)

        sqllist = sqltext.replace('\r\n', ' ').replace('\n', ' ').replace(';', ';-*-*-*-').split('-*-*-*-')
        dbnamelist = []
        alldb = db.session.query(Dbs.name).all()
        for sql in sqllist:
            tmp_sql = str(sql).replace('`', '').lstrip()
            if str.lower(tmp_sql).startswith('insert'):
                db_tbname = re.findall(r"insert *into *([\w]*\.[\w]*).*", tmp_sql, re.M | re.IGNORECASE)
                dbname = ''.join(db_tbname).split('.')[0]

    return render_template('workorder/MineWorkorder/MineWorkorder.html')
