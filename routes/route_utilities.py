#!/usr/bin/env python
import extensions
import models
import uuid

from flask import abort, g, request
from sqlalchemy import and_

auth = extensions.auth
db = extensions.db
AuthToken = models.AuthToken
dataResultSuccess = extensions.dataResultSuccess

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


def table_get(model):
    params = request.args.to_dict()
    filters = extensions.queryToJson(params.pop('query')) if 'query' in params else {}
    filterList = []
    itemList = []
    for key, value in filters.items():
        column = getattr(model, key, None)
        columnFilter = column.like(value)
        filterList.append(columnFilter)
    queryItems = model.query.filter(and_(*filterList)).all()
    for item in queryItems:
        itemList.append(item.to_dict())
    return dataResultSuccess(itemList, spuriousParameters=list(params.keys()), count=len(itemList))


def table_ins(model):
    requestJson = request.get_json(force=True)
    item = model(**requestJson)
    item.gid = item.gid or uuid.uuid4()
    db.session.add(item)
    db.session.commit()
    return dataResultSuccess(item.to_dict(), code=201, spuriousParameters=list(request.args.to_dict().keys()))


def table_update(model):
    args = request.args.to_dict()
    gid = args.pop('gid') if 'gid' in args else abort(400)  # TODO make this work with ID as well (maybe anything unique if you have time)
    body = request.get_json(force=True)
    item = table_item_get_gid(model, gid)
    item.set_columns(**body)
    return dataResultSuccess(item.to_dict(), code=200, spuriousParameters=list(args.keys()))


def table_delete(model):
    args = request.args.to_dict()
    gid = args.pop('gid') if 'gid' in args else abort(400)  # TODO make this work with ID as well (maybe anything unique if you have time)
    item = table_item_get_gid(model, gid)
    db.session.delete(item)
    db.session.commit()
    return ('Item Deleted', 200)


def table_item_get_gid(model, guid):
    item = model.query.filter_by(gid=guid).first()
    if (item is None):
        abort(404)
    return item
