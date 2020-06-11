#!/usr/bin/env python
import extensions
from models import Employee, Hotel

from flask import request, Blueprint
from routes.route_utilities import table_get, table_ins, table_update, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess

employee_blueprint = Blueprint("employee", __name__, url_prefix='/employee')


@auth.login_required(1)
@employee_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'DELETE'], endpoint='employee')
def endpoint_employee():
    if (request.method == 'POST'):
        return table_ins(Employee)
    elif (request.method == 'GET'):
        return table_get(Employee)
    elif (request.method == 'PATCH'):
        return table_update(Employee)
    else:
        return table_delete(Employee)


@auth.login_required(1)
@employee_blueprint.route('/hotels', methods=['GET', 'POST', 'PATCH', 'DELETE'], endpoint='employee_hotel')
def employee_hotel():
    # TODO support multiple hotels
    returnHotel = Hotel.query.first()
    if (returnHotel is not None):
        return dataResultSuccess([{"hotelname": returnHotel.name, "hotelrefno": returnHotel.hotelrefno}])
    else:
        return dataResultSuccess([{"hotelname": "No Hotel", "hotelrefno": 0}])
