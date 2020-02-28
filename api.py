#!/usr/bin/env python
import os
import sys
import time
import json
import random
from passlib.hash import pbkdf2_sha512 as sha512
from flask import Flask, abort, request, jsonify, g, url_for
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown dog jumps over the lazy fox'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite' #TODO use MySQL (it'll probably work fine)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPTokenAuth()
apiPrefix = '/forest'

#TODO split this stuff into a different py file and amke sure no circular dependencies
class AuthToken(db.Model):
    __tablename__ = 'auth_token'
    id = db.Column (db.Integer, primary_key=True)
    token_type = db.Column(db.String(40), default='bearer')
    access_token = db.Column(db.String(64), unique=True, nullable=False)
    refresh_token = db.Column(db.String(64), index=True)
    revoked = db.Column(db.Boolean, default=False)
    issued_at = db.Column(db.Integer, nullable=False, default=lambda: int(time.time()))
    expires_in = db.Column(db.Integer, nullable=False, default=86400)
    user_id = db.Column(db.Integer, db.ForeignKey('api_user.id', ondelete='CASCADE'))
    user = db.relationship('APIUser')

    def get_expires_in(self):
        return self.expires_in

    def get_expires_at(self):
        return self.issued_at + self.expires_in

    def get_is_expired(self):
        return self.get_expires_at <= int(time.time())

    @staticmethod
    def generate_token():
        return ''.join([str(y) for x in range(64) for y in random.choice('0123456789abcdef')])

    def generate_token_set(self):
        self.access_token = self.generate_token()
        self.refresh_token = self.generate_token()
        self.revoked = False
        self.issued_at = int(time.time())
        return True

    def generate_token_access(self):
        self.access_token = generate_token()
        self.issued_at = int(time.time())
        return True

class APIUser(db.Model):
    __tablename__ = 'api_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))
    admin = db.Column(db.Boolean, default=False, nullable=False)

    def hash_password(self, password):
        self.password_hash = sha512.hash(password)

    def verify_password(self, password):
        return sha512.verify(password, self.password_hash)

#------------------------------------------------------------------------

db.create_all()
db.session.commit()


#TODO figure out this g.user stuff and how it works, then edit this method to only work with tokens
#This method seems to be called on everything that has [@auth.login_required], if this returns true, the method gets executed, otherwise a 401 is returned
@auth.verify_token
def verify_token(token):
    ## first try to authenticate by token
    #user = APIUser.verify_auth_token(username_or_token)
    #if not user:
        ## try to authenticate with username/password
        #user = APIUser.query.filter_by(username=username_or_token).first()
        #if not user or not user.verify_password(password):
            #return False
    #g.user = user
    return True

#TODO require admin status to be able to make this
@app.route(apiPrefix+'/users', methods=['POST'])
def new_user():
    username = request.get_json(force = True)['username']
    password = request.get_json(force = True)['password']
    if username is None or password is None:
        abort(400)    # missing arguments
    if APIUser.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = APIUser(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})

#TODO remove
@app.route('/api/users/<int:id>')
def get_user(id):
    user = APIUser.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})

#TODO remove
@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

#TODO replace with proper endpoints once testing is done
@app.route(apiPrefix+'/resource')
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, World!'})

@app.route(apiPrefix+'/auth/login', methods=['POST'])
def post_login():
    grant_type = request.get_json(force = True)['grant_type']
    #check grant type
    if (grant_type == 'password'):
        #if pass login check password hash
        username = request.get_json(force = True)['username']
        password = request.get_json(force = True)['password']
        if (username is None or password is None):
            abort(400)    # missing arguments

        username = username.split('@')[0]   #if an email is recireved, get only the first part (good job failing that Hotech!!)

        loginAPIUser = APIUser.query.filter_by(username=username).first()
        if (not loginAPIUser or not loginAPIUser.verify_password(password)):
            abort(400) #incorrect password / username
        #if pass hash correct check if user token set is expired
        userToken = AuthToken.query.filter_by(user_id=loginAPIUser.id).first()
        #if no token is found, make one
        if (userToken is None):
            userToken = AuthToken()
            userToken.generate_token_set()
            db.session.add(userToken)
            db.session.commit()
        #if revoked generate new token set
        elif (userToken.revoked): userToken.generate_token_set()
        #elif expired generate new auth token and reset timer
        elif (userToken.get_is_expired()): userToken.generate_token_access()
        #return token set
        aToken = userToken.access_token
        rToken = userToken.refresh_token
        exp = userToken.expires_in
        tType = userToken.token_type
        return jsonify({'access_token':aToken,
                        'refresh_token':rToken,
                        'token_type':tType,
                        'expires_in':exp})

    elif (grant_type == 'refresh_token'):
        #if token login check refresh token
        userToken = AuthToken.query.filter_by(refresh_token = request.json.get('refresh_token'))
        #if it matches generate a new auth token and reset timer
        #if revoked or no match return 400
        if (userToken is None): abort(400)
        else:
            userToken.generate_token_set()
            aToken = userToken.access_token
            rToken = userToken.refresh_token
            exp = userToken.expires_in
            tType = userToken.token_type
            return jsonify({'access_token':aToken,
                            'refresh_token':rToken,
                            'token_type':tType,
                            'expires_in':exp})
    else:
        abort(400)
        return null

#TODO figure out this app.run stuff and how it works, then split into a different py if possible
app.run(debug=True)
