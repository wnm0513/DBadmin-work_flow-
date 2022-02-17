from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import hashlib
from useddb.models import User

from . import Login


@Login.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.filter(User.id == user_id).first()
