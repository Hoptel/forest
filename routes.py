#!/usr/bin/env python
from flask import abort, request, jsonify, g, url_for, Blueprint

import extensions
import models
import time


auth = extensions.auth
db = extensions.db
APIUser = models.APIUser
AuthToken = models.AuthToken

blueprint = Blueprint("forest", __name__, url_prefix="/forest")

# TODO edit this method to only work with tokens
# This method seems to be called on everything that has [@auth.login_required],
# if this returns true, the method gets executed, otherwise a 401 is returned
@auth.verify_token
def verify_token(token):
    # Getting the token
    userToken = AuthToken.query.filter_by(access_token=token).first()
    if (userToken is None or userToken.get_is_invalid()):
        abort(401)
    g.userID = userToken.user_id
    g.authLevel = userToken.scope
    return True


# TODO require admin status to be able to make this
@blueprint.route('/users', methods=['POST'])
def new_user():
    requestJson = request.get_json(force=True)
    username = requestJson['username']
    password = requestJson['password']
    if username is None or password is None:
        abort(400)    # missing arguments
    if APIUser.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = APIUser(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201, {'Location': url_for('forest.get_user', id=user.id, _external=True)})


# TODO remove
@blueprint.route('/users/<int:id>')
def get_user(id):
    user = APIUser.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


# TODO replace with proper endpoints once testing is done
@blueprint.route('/resource')
@auth.login_required
def get_resource():
    return extensions.dataResultSuccess('Hello ' + APIUser.query.filter_by(id=g.userID).first().username)


@blueprint.route('/auth/login', methods=['POST'])
def post_login():
    grant_type = request.get_json(force=True)['grant_type']
    # check grant type
    if (grant_type == 'password'):
        # if pass login check password hash
        username = request.get_json(force=True)['username']
        password = request.get_json(force=True)['password']
        if (username is None or password is None):
            abort(400)    # missing arguments
        # if an email is recireved, get only the first part (good job failing that Hotech!!)
        username = username.split('@')[0]

        loginAPIUser = APIUser.query.filter_by(username=username).first()
        if (not loginAPIUser or not loginAPIUser.verify_password(password)):
            abort(400)  # incorrect password / username
        # if pass hash correct check if user token set is expired
        userToken = AuthToken.query.filter_by(user_id=loginAPIUser.id).first()
        # if no token is found, make one
        if (userToken is None):
            userToken = AuthToken()
            userToken.generate_token_set(loginAPIUser)
            db.session.add(userToken)
            db.session.commit()
        # if revoked generate new token set
        elif (userToken.revoked):
            userToken.generate_token_set(loginAPIUser)
        # elif expired generate new auth token and reset timer
        elif (userToken.get_is_expired()):
            userToken.generate_token_access()
        # return token set
        aToken = userToken.access_token
        rToken = userToken.refresh_token
        exp = userToken.get_expires_at() - int(time.time())
        tType = userToken.token_type
        return jsonify({'access_token': aToken,
                        'refresh_token': rToken,
                        'token_type': tType,
                        'expires_in': exp})

    elif (grant_type == 'refresh_token'):
        # if token login check refresh token
        userToken = AuthToken.query.filter_by(
            refresh_token=request.json.get('refresh_token'))
        # if it matches generate a new auth token and reset timer
        # if revoked or no match return 400
        if (userToken is None):
            abort(400)
        else:
            userToken.generate_token_set(userToken.user)
            aToken = userToken.access_token
            rToken = userToken.refresh_token
            exp = userToken.get_expires_at() - int(time.time())
            tType = userToken.token_type
            return jsonify({'access_token': aToken,
                            'refresh_token': rToken,
                            'token_type': tType,
                            'expires_in': exp})
    else:
        abort(400)
        return None
