import extensions
import models
import uuid

from flask import request, g, Blueprint
from routes.route_utilities import table_get

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess
resultSuccess = extensions.resultSuccess
resultFailure = extensions.resultFailure
APIUser = models.User
AuthToken = models.AuthToken

user_blueprint = Blueprint("user", __name__, url_prefix="/user")


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


@auth.login_required(2)
def query_user():
    return table_get(APIUser)


def new_user():  # TODO require admin status to be able to make this
    requestJson = request.get_json(force=True)
    username = requestJson['username']
    password = requestJson['password']
    if username is None or password is None:
        return resultFailure(msg='Missing Data', code=400)    # missing arguments
    if APIUser.query.filter_by(username=username).first() is not None:
        return resultFailure(msg='Existing User', code=400)    # existing user
    user = APIUser(**requestJson)
    user.hash_password(password)
    user.guid = user.guid or uuid.uuid4()
    db.session.add(user)
    db.session.commit()
    return dataResultSuccess(user.to_dict(), code=201, spuriousParameters=list(request.args.to_dict().keys()))


@auth.login_required(1)
def update_user():  # TODO require an admin or the user himself to do this
    args = request.args.to_dict()
    body = request.get_json(force=True)
    user = None
    if (g.authLevel > 1):
        if ('guid' in args):
            guid = args.pop('guid')
            user = APIUser.query.filter_by(guid=guid).first()
        elif ('id' in args):
            uid = args.pop('id')
            user = APIUser.query.filter_by(id=uid).first()
        else:
            user = g.user
        if (user is None):
            resultFailure("No user found.", 404)
    else:
        user = g.user
    user.set_columns(**body)
    if ('password' in body):
        user.hash_password(body['password'])
        userToken = AuthToken.filter_by(user=user).first()
        userToken.revoked = True
    return dataResultSuccess(user.to_dict(), code=200, spuriousParameters=list(args.keys()))


@auth.login_required(1)
def delete_user():
    args = request.args.to_dict()
    user = None
    if (g.authLevel > 1):
        if ('guid' in args):
            guid = args.pop('guid')
            user = APIUser.query.filter_by(guid=guid).first()
        elif ('id' in args):
            uid = args.pop('id')
            user = APIUser.query.filter_by(id=uid).first()
        else:
            user = g.user
        if (user is None):
            resultFailure("No user found.", 404)
    else:
        user = g.user
        token = AuthToken.query.filter_by(userid=user.id).first()
        db.session.delete(user)
        db.session.delete(token)
        db.session.commit()
    return extensions.resultSuccess(msg="Item deleted", code=200, spuriousParameters=list(args.keys()))


@user_blueprint.route('/info')
@auth.login_required(1)
def get_user_info():
    return dataResultSuccess({
        'authlevel': g.authLevel,
        'code': g.user.code or g.user.username,
        'email': g.user.email,
        'guid': g.user.guid,
        # 'hotelrefno': g.user.hotelrefno,
        'userid': g.user.id,
        # 'shortcode': g.user.shortcode,
    }, spuriousParameters=list(request.args.to_dict().keys()))

# TODO replace with proper endpoints once testing is done
@user_blueprint.route('/resource')
@auth.login_required(3)
def get_resource():
    return dataResultSuccess('Hello ' + g.user.username)
