#!/usr/bin/env python
import extensions
import models
import time

from flask import abort, request, jsonify, g, Blueprint

auth = extensions.auth
db = extensions.db
APIUser = models.APIUser
AuthToken = models.AuthToken

auth_blueprint = Blueprint("auth", __name__, url_prefix="/forest/auth")


@auth_blueprint.route('/login', methods=['POST'])
def post_login():
    grant_type = request.get_json(force=True)['grant_type']
    # check grant type
    if (grant_type == 'password'):
        # if pass login check password hash
        username = request.get_json(force=True)['username']
        password = request.get_json(force=True)['password']
        if (username is None or password is None):
            abort(400)    # missing arguments
        # if an email is received, get only the first part (good job failing that Hotech!!)
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
            refresh_token=request.json.get('refresh_token')).first()
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


@auth_blueprint.route('/logout')
@auth.login_required
def logout():
    g.user.revoked = True
