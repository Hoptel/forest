#!/usr/bin/env python
from flask import abort, request, jsonify, g, url_for, Blueprint, send_from_directory

import extensions
import models
import time
import os
import uuid

import json


auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess
APIUser = models.APIUser
AuthToken = models.AuthToken

blueprint = Blueprint("forest", __name__, url_prefix="/forest")

# This method seems to be called on everything that has [@auth.login_required],
# if this returns true, the method gets executed, otherwise a 401 is returned
@auth.verify_token
def verify_token(token):
    # Getting the token
    userToken = AuthToken.query.filter_by(access_token=token).first()
    if (userToken is None or userToken.get_is_invalid()):
        abort(401)
    g.user = userToken.user
    g.authLevel = userToken.scope
    return True


# TODO require admin status to be able to make this
@blueprint.route('/user', methods=['POST'])
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
    user.gid = uuid.uuid4()
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201, {'Location': url_for('forest.get_user', id=user.id, _external=True)})


@blueprint.route('/user/info')
@auth.login_required
def get_user_info():
    return dataResultSuccess({
        'authlevel': g.authLevel,
        'code': g.user.username,
        'email': g.user.email,
        'gid': g.user.gid,
        # 'hotelrefno': g.user.hotelrefno,
        'userid': g.user.id,
        # 'shortcode': g.user.shortcode,
    }, spuriousParameters=list(request.args.to_dict().keys()))


# TODO replace with proper endpoints once testing is done
@blueprint.route('/resource')
@auth.login_required
def get_resource():
    return dataResultSuccess('Hello ' + g.user.username)


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


@blueprint.route('/auth/logout')
@auth.login_required
def logout():
    g.user.revoked = True

# TODO maybe make this its own blueprint and separate blueprints
@blueprint.route('/dbfile/load', methods=['GET', 'POST'])
@auth.login_required
def load():
    # uploading
    if (request.method == 'POST'):
        uploaded_files = request.files.getlist('file')
        # getting all the parameters
        params = request.args.to_dict()
        masterID = None
        # removing the masterid paramerter if it is there
        if ('masterid' in params):
            masterID = params.pop('masterid')
        # if not, then use the user's gid
        else:
            masterID = g.user.gid
        fileList = []
        for file in uploaded_files:
            fileNameList = file.filename.split('.')
            filename = fileNameList[0]
            fileext = fileNameList[1]
            fileItem = models.DBFile(masterid=masterID, gid=uuid.uuid4(), filename=filename, filetype=fileext)
            if (masterID is not None):
                os.makedirs(os.path.dirname(__file__) + "/storage/dbfile", str(masterID), exist_ok=True)
                file.save(os.path.join(
                    os.path.dirname(__file__) + '/storage/dbfile', str(masterID), str(fileItem.gid) + '.' + fileext))
            else:
                os.makedirs(os.path.dirname(__file__) + "/storage/dbfile", exist_ok=True)
                file.save(os.path.join(
                    os.path.dirname(__file__) + '/storage/dbfile/', str(fileItem.gid) + '.' + fileext))
            db.session.add(fileItem)
            fileList.append(file.filename)
        db.session.commit()
        # returning the normal response + getting the non popped parameters into spurious
        return extensions.dataResultSuccess(
            fileList, count=len(uploaded_files), spuriousParameters=list(params.keys()), code=201)
    else:
        arguments = request.args.to_dict()
        dbFileItem = None
        if ('id' in arguments):
            dbFileItem = models.DBFile.query.filter_by(id=arguments['id']).first()
        elif ('gid' in arguments):
            dbFileItem = models.DBFile.query.filter_by(gid=arguments['gid']).first()
        elif ('masterid' in arguments & 'code' in arguments):
            dbFileItem = models.DBFile.query.filter_by(masterid=arguments['masterid'], code=arguments['code']).first()
        else:
            abort(400)
        if (dbFileItem is None):
            abort(404)
        return send_from_directory(os.path.join(
            os.path.dirname(__file__),
            'storage/dbfile',
            str(dbFileItem.masterid)),
            (str(dbFileItem.gid) + '.' + dbFileItem.filetype))


@blueprint.route('/table')
def parameter():
    queryparam = request.args.to_dict()['query']
    newQueryParam = "{"
    queryparam = queryparam.replace(' ', '')  # Remove all whitespaces
    queryList = queryparam.split(',')  # split the string into queries
    for part in queryList:
        subParts = part.split(':')  # further split things into key, value pairs
        newQueryParam += '"' + subParts[0] + '":"' + subParts[1] + '",'  # reconstruct the key value pairs in the new parameter
    newQueryParam = newQueryParam[:-1]  # remove the last trailing comma
    newQueryParam += '}'  # finish by adding the closing bracket
    print(newQueryParam)
    return json.loads(newQueryParam)
