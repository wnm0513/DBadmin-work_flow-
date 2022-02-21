from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from app import login_required
from . import OrderHistories


@OrderHistories.route('/OrderHistories')
@login_required
def OrderHistory():
    return render_template('workorder/OrderHistory/OrderHistory.html')