#!/usr/bin/env python
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
auth = HTTPTokenAuth()
