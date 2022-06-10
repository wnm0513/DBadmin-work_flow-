import functools

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)


# 在其他视图中验证
# 用户登录以后才能进行功能的使用。
# 在每个视图中可以使用 装饰器 来完成这个工作
def login_required(view):
    # 装饰器返回一个新的视图，该视图包含了传递给装饰器的原视图
    @functools.wraps(view)
    # 新的函数检查用户是否载入。
    # 如果已载入，那么就继续正常执行原视图
    def wrapped_view(**kwargs):
        # 否则就重定向到登录页面
        if g.user is None:
            return redirect(url_for('login.login'))

        return view(**kwargs)

    return wrapped_view
