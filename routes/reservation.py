#!/usr/bin/env python
import extensions
from models import Reservation

from flask import request, Blueprint
from routes.route_utilities import table_get, table_ins, table_update, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess

reservation_blueprint = Blueprint("reservation", __name__, url_prefix='/reservation')


@auth.login_required(1)
@reservation_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def endpoint_employee():
    if (request.method == 'POST'):
        return table_ins(Reservation)
    elif (request.method == 'GET'):
        return table_get(Reservation)
    elif (request.method == 'PATCH'):
        return table_update(Reservation)
    else:
        return table_delete(Reservation)
