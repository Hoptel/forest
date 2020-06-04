#!/usr/bin/env python
import extensions
from models import RoomType

from flask import request, Blueprint
from routes.route_utilities import table_get, table_ins, table_update, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess

roomtype_blueprint = Blueprint("roomtype", __name__, url_prefix='/roomtype')


@auth.login_required(1)
@roomtype_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def endpoint_employee():
    if (request.method == 'POST'):
        return table_ins(RoomType)
    elif (request.method == 'GET'):
        return table_get(RoomType)
    elif (request.method == 'PATCH'):
        return table_update(RoomType)
    else:
        return table_delete(RoomType)
