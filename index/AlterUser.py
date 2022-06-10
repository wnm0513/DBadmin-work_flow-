import datetime
import os
import time

from PIL import Image
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import hashlib

from login_required import login_required
from useddb.models import User, db
from config import Config

from . import Index_AlterUser


# 修改用户信息
@Index_AlterUser.route('/AlterUserinfo', methods=['GET', 'POST'])
@login_required
def AlterUserinfo():
    # 获取用户信息
    user = User.query.filter_by(account=g.user.account).first()
    # 确认更改
    if request.method == 'POST':
        dingding = request.form.get('dingding')
        phone = request.form.get('phone')
        email = request.form.get('email')

        user.ding = dingding
        user.phone = phone
        user.email = email
        user.utime = datetime.datetime.now()

        # 提交信息
        db.session.add(user)
        try:
            db.session.commit()
            error = 'Alter successfully.'

        except Exception as e:
            db.session.rollback()
            db.session.flush()
            error = str(e)

        flash(error)
    return render_template('AlterUserinfo.html')


# 修改用户头像
@Index_AlterUser.route('/AlterUserprofile', methods=['GET', 'POST'])
@login_required
def AlterUserprofile():
    # 获取用户信息
    re_filename = None
    user = User.query.filter_by(account=g.user.account).first()
    if request.method == 'POST':
        user_profile = request.files.get('user_profile')
        path = Config.INCEPTION_UPATH
        if not path:
            os.makedirs(path)

        # 检测文件格式
        if user_profile and '.' in user_profile.filename and user_profile.filename.split('.')[
            -1] in Config.UPLOADED_PROFILE_ALLOW:
            # 存储图片文件
            # 获取当前时间戳（毫秒）
            current_time = int(round(time.time() * 1000))
            current_day = time.strftime("%Y%m%d", time.localtime(time.time()))
            re_filename = str(g.user.account) + str(current_day) + str(current_time) + '.jpg'
            user_profile.save(os.path.join(path, re_filename))

            # 记录修改时间,并更新数据库中头像对应的文件名
            user.utime = datetime.datetime.now()
            user.profile = re_filename
            db.session.add(user)
            try:
                db.session.commit()
                error = 'Alter successfully.'
            except Exception as e:
                db.session.rollback()
                db.session.flush()
                error = str(e)

        else:
            error = '文件名不合法,请上传jpg、png、jpeg图片'

        flash(error)

        return render_template('AlterUserprofile.html', re_filename=re_filename)

    return render_template('AlterUserprofile.html')
