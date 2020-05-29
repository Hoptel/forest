#!/usr/bin/env python
import extensions
from models import Sale

from flask import request, Blueprint
from routes.route_utilities import table_get, table_ins, table_update, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess

sale_blueprint = Blueprint("sale", __name__, url_prefix='/sale')


@auth.login_required(1)
@sale_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'UPDATE'])
def endpoint_employee():
    if (request.method == 'POST'):
        return table_ins(Sale)
    elif (request.method == 'GET'):
        return table_get(Sale)
    elif (request.method == 'PATCH'):
        return table_update(Sale)
    else:
        return table_delete(Sale)
