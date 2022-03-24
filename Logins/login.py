import datetime

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import hashlib
from useddb.models import User, db

from . import Login


@Login.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form.get('account')
        password = request.form.get('password')
        remember = request.form.get('remember')

        m1 = hashlib.md5()
        m1.update(password.encode("utf8"))
        pwd_md5 = m1.hexdigest()
        user = User.query.filter(User.account == account).first()

        if user:
            if user.status == 0:
                error = '账号未被启用，请联系管理员进行激活'

            elif user.passwd == pwd_md5:
                # 记录登录时间
                user.last_login = datetime.datetime.now()
                db.session.add(user)
                db.session.commit()
                # 取出用户id作为全局变量
                if remember == '1':
                    session.permanent = True
                    session['user_id'] = user.id
                    return redirect(url_for('index'))
                else:
                    session.clear()
                    session['user_id'] = user.id
                    return redirect(url_for('index'))

            else:
                error = '密码错误，请确认后再登录'

        else:
            error = '账号错误，请确认后再登录'

        flash(error)

    return render_template('Login/login.html')


@Login.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login.login'))


@Login.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        account = request.form.get('account')
        password = request.form.get('password')
        password_again = request.form.get('password_again')
        code = request.form.get('code')
        m1 = hashlib.md5()
        m1.update(password.encode("utf8"))
        pwd_md5 = m1.hexdigest()
        if password != password_again:
            error = '两次输入的密码不一致，请确认'
            flash(error)
            return render_template('Login/reset_password.html')

        user = User.query.filter(User.account == account).first()
        if user:
            if user.status == 0:
                error = '账号未被启用，请联系管理员进行激活'

            elif code == 'banksteel':
                # 记录修改时间
                user.utime = datetime.datetime.now()
                user.passwd = pwd_md5
                db.session.add(user)
                db.session.commit()
                # 取出用户id作为全局变量
                session.clear()
                session['user_id'] = user.id
                return redirect(url_for('login.login'))

            else:
                error = '验证错误，请确认后再修改'

        else:
            error = '账号错误，请确认'

        flash(error)

    return render_template('Login/reset_password.html')
