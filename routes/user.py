#!/usr/bin/env python
import extensions
import models
import uuid

from flask import abort, request, g, Blueprint
from routes.route_utilities import table_get, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess
APIUser = models.APIUser
AuthToken = models.AuthToken

user_blueprint = Blueprint("user", __name__, url_prefix="/forest/user")


@user_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def endpoint_user():
    if (request.method == 'POST'):
        return new_user()
    elif (request.method == 'GET'):
        return query_user()
    elif (request.method == 'PATCH'):
        return update_user()
    else:
        return delete_user()


def query_user():  # TODO make this a general function
    return table_get(APIUser)


def new_user():  # TODO require admin status to be able to make this
    requestJson = request.get_json(force=True)
    username = requestJson['username']
    password = requestJson['password']
    if username is None or password is None:
        return('Missing Data', 400)    # missing arguments
    if APIUser.query.filter_by(username=username).first() is not None:
        return('Existing User', 400)    # existing user
    user = APIUser(**requestJson)
    user.hash_password(password)
    user.gid = user.gid or uuid.uuid4()
    db.session.add(user)
    db.session.commit()
    return dataResultSuccess(user.to_dict(), code=201, spuriousParameters=list(request.args.to_dict().keys()))

# TODO the next 2 methods share a lot of similar code, maybe turn the shared code into a function


def update_user():  # TODO require an admin or the user himself to do this
    args = request.args.to_dict()
    body = request.get_json(force=True)
    gid = args.pop('gid') if 'gid' in args else abort(400)  # TODO make this work with ID as well (maybe anything unique if you have time)
    user = APIUser.query.filter_by(gid=gid).first()
    if (user is None):
        abort(404)
    user.set_columns(**body)
    if ('password' in body):
        user.hash_password(body['password'])
    return dataResultSuccess(user.to_dict(), code=200, spuriousParameters=list(args.keys()))


def delete_user():
    return table_delete(APIUser)


@user_blueprint.route('/info')
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
@user_blueprint.route('/resource')
@auth.login_required
def get_resource():
    return dataResultSuccess('Hello ' + g.user.username)
