#!/usr/bin/env python
import extensions
from models import Cost

from flask import request, Blueprint
from routes.route_utilities import table_get, table_ins, table_update, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess

cost_blueprint = Blueprint("cost", __name__, url_prefix='/cost')


@auth.login_required(1)
@cost_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'UPDATE'])
def endpoint_employee():
    if (request.method == 'POST'):
        return table_ins(Cost)
    elif (request.method == 'GET'):
        return table_get(Cost)
    elif (request.method == 'PATCH'):
        return table_update(Cost)
    else:
        return table_delete(Cost)
