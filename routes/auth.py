import extensions
import models
import time

from flask import request, jsonify, Blueprint

auth = extensions.auth
db = extensions.db
APIUser = models.User
AuthToken = models.AuthToken
resultFailure = extensions.resultFailure
resultSuccess = extensions.resultSuccess

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@auth_blueprint.route('/login', methods=['POST'])
def post_login():
    grant_type = request.get_json(force=True)['grant_type']
    # check grant type
    if (grant_type == 'password'):
        # if pass login check password hash
        username = request.get_json(force=True)['username']
        password = request.get_json(force=True)['password']
        if (username is None or password is None):
            resultFailure("missing arguments.", 400)    # missing arguments
        loginAPIUser = None
        if ('@' in username and '.' in username):
            loginAPIUser = APIUser.query.filter_by(email=username).first()
            if (loginAPIUser is None):
                loginAPIUser = APIUser.query.filter_by(username=username).first()
        else:
            loginAPIUser = APIUser.query.filter_by(username=username).first()
        if (not loginAPIUser or not loginAPIUser.verify_password(password)):
            resultFailure("Incorrect username / password", 400)  # incorrect password / username
        # if pass hash correct check if user token set is expired
        userToken = AuthToken.query.filter_by(userid=loginAPIUser.id).first()
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
        scope = userToken.scope
        return jsonify({'access_token': aToken,
                        'refresh_token': rToken,
                        'token_type': tType,
                        'expires_in': exp,
                        'scope': scope})

    elif (grant_type == 'refresh_token'):
        # if token login check refresh token
        if (request.json.get('refresh_token') is None):
            resultFailure("No refresh token recieved.", 400)
        userToken = AuthToken.query.filter_by(refresh_token=request.json.get('refresh_token')).first()
        # if revoked or no match return 400
        if (userToken is None or userToken.revoked):
            resultFailure("RefreshToken invalid.", 400)
        # if it matches generate a new auth token and reset timer
        else:
            userToken.generate_token_set(userToken.user)
            aToken = userToken.access_token
            rToken = userToken.refresh_token
            exp = userToken.get_expires_at() - int(time.time())
            tType = userToken.token_type
            scope = userToken.scope
            return jsonify({'access_token': aToken,
                            'refresh_token': rToken,
                            'token_type': tType,
                            'expires_in': exp,
                            'scope': scope})
    else:
        resultFailure("incorrect grant type", 400)
        return None


@auth_blueprint.route('/logout')
def logout():
    auth_type, token = request.headers['Authorization'].split(None, 1)
    if (token is None):
        resultFailure("No token recieved.", 401)
    tokenItem = AuthToken.query.filter_by(access_token=token).first()
    tokenItem.revoked = True
    db.session.commit()
    return resultSuccess(msg='Logout successful.', code=200)
