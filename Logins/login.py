from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import hashlib
from useddb.models import User

from . import Login


@Login.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form.get('account')
        password = request.form.get('password')
        m1 = hashlib.md5()
        m1.update(password.encode("utf8"))
        pwd_md5 = m1.hexdigest()
        user = User.query.filter(User.account == account).first()

        if user:
            if user.passwd == pwd_md5:
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

