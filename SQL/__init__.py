from flask import Blueprint

sqlExecutes = Blueprint('sqlExecute', __name__)

RedisExecutes = Blueprint('RedisExecute', __name__)

sqlHistories = Blueprint('sqlHistory', __name__)

RedisExecutesHistory = Blueprint('RedisExecuteHistory', __name__)
