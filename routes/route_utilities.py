import extensions
import models
import uuid

from flask import g, request
from sqlalchemy import and_, or_

auth = extensions.auth
db = extensions.db
AuthToken = models.AuthToken
dataResultSuccess = extensions.dataResultSuccess
resultFailure = extensions.resultFailure
resultSuccess = extensions.resultSuccess


# This method seems to be called on everything that has [@auth.login_required],
# if this returns true, the method gets executed, otherwise a 401 is returned
@auth.verify_token
def verify_token(token, auth_level):
    # Getting the token
    token_actual = request.headers['Authorization'].split(" ", 1)[1]
    userToken = AuthToken.query.filter_by(access_token=token_actual).first()
    if (userToken is None):
        resultFailure("Token not found.", 401)
    if (userToken.get_is_invalid()):
        resultFailure("Token invalid.", 401)
    elif(userToken.scope < auth_level):
        resultFailure("Token access level insufficient.", 401)
    g.user = userToken.user
    g.authLevel = userToken.scope
    return True


def table_get(model, custom_filters={}):
    params = request.args.to_dict()
    filters = extensions.queryToJson(params.pop('query')) if 'query' in params else {}
    filterList = []
    itemList = []
    # adding the custom filters
    filters = {**filters, **custom_filters}
    # check if "private" exists here
    if (hasattr(model, 'private')):
        column = getattr(model, 'private', None)
        columnFilter = column.is_(False)
        filterList.append(columnFilter)
    for key, value in filters.items():
        column = getattr(model, key, None)
        columnFilter = column.like(value)
        filterList.append(columnFilter)
    queryItems = model.query.filter(and_(*filterList)).all()
    for item in queryItems:
        itemList.append(item.to_dict())
    return dataResultSuccess(itemList, spuriousParameters=list(params.keys()), count=len(itemList))


# Return one item from the database based on the ID or the GUID, ID takes precendence if both are provided
def table_get_single(model, id=None, guid=None):
    params = request.args.to_dict()
    queryItem = None
    if (id is not None):
        queryItem = model.query.filter_by(id=id).first()
    elif (guid is not None):
        queryItem = model.query.filter_by(guid=guid).first()
    else:
        resultFailure("no identifier recieved, provide ID or GUID.", 400)
    if (queryItem is None):
        resultFailure("Item not found.", 404)
    return dataResultSuccess(queryItem.to_dict(), spuriousParameters=list(params.keys()))


def table_ins(model, requestBody=None):
    requestJson = requestBody or request.get_json(force=True)
    item = model(**requestJson)
    item.guid = item.guid or uuid.uuid4()
    db.session.add(item)
    db.session.commit()
    return dataResultSuccess(item.to_dict(), code=201, spuriousParameters=list(request.args.to_dict().keys()))


def table_update(model, requestArgs=None):
    args = requestArgs or request.args.to_dict()
    guid = args.pop('guid') if 'guid' in args else resultFailure("GUID not provided", 400)  # TODO make this work with ID as well (maybe anything unique if you have time)
    body = request.get_json(force=True)
    item = table_item_get_guid(model, guid)
    if (g.authLevel >= 2 or g.authLevel == 1 and g.user.id == item.userid):
        item.set_columns(**body)
        return dataResultSuccess(item.to_dict(), code=200, spuriousParameters=list(args.keys()))
    else:
        resultFailure("You do not own this item.", 401)


def table_delete(model):
    args = request.args.to_dict()
    guid = args.pop('guid') if 'guid' in args else resultFailure("GUID not provided", 400)  # TODO make this work with ID as well (maybe anything unique if you have time)
    item = table_item_get_guid(model, guid)
    if (g.authLevel >= 2 or g.authLevel == 1 and g.user.id == item.userid):
        db.session.delete(item)
        db.session.commit()
        return resultSuccess(msg="Item deleted", code=200, spuriousParameters=list(args.keys()))
    else:
        resultFailure("You do not own this item.", 401)


def table_multiQuery(model):
    params = request.args.to_dict()
    queryparam = params.pop('query') if 'query' in params else resultFailure("Query not provided", 400)
    filterList = []
    privateFilter = None
    itemList = []
    if (hasattr(model, 'private')):
        column = getattr(model, 'private', None)
        privateFilter = column.is_(False)
    for key in model.__table__.columns.keys():
        if hasattr(model, '_hidden_fields'):
            hidden = model._hidden_fields
            if (key in hidden):
                continue
        column = getattr(model, key, None)
        if (column.type.python_type is type(queryparam)):
            columnFilter = column.contains(queryparam)
            filterList.append(columnFilter)
    queryItems = model.query.filter(privateFilter & or_(*filterList)).all()
    for item in queryItems:
        itemList.append(item.to_dict())
    return dataResultSuccess(itemList, spuriousParameters=list(params.keys()), count=len(itemList))


def table_item_get_guid(model, guid):
    item = model.query.filter_by(guid=guid).first()
    if (item is None):
        resultFailure("Item not found.", 404)
    return item
