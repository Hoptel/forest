#!/usr/bin/env python
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify

db = SQLAlchemy()
auth = HTTPTokenAuth()


def dataResultSuccess(data, msg="", spuriousParameters=[], count=1):
    return (jsonify({"success": True, "msg": msg, "spurious-parameters": spuriousParameters, "data": data, "count": count}), 200)
