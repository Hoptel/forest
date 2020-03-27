#!/usr/bin/env python
import extensions
from models import Employee

from flask import request, Blueprint
from routes.route_utilities import table_get, table_ins, table_update, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess

employee_blueprint = Blueprint("employee", __name__, url_prefix='/forest/employee')


@auth.login_required
@employee_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'UPDATE'])
def endpoint_employee():
    if (request.method == 'POST'):
        return table_ins(Employee)
    elif (request.method == 'GET'):
        return table_get(Employee)
    elif (request.method == 'PATCH'):
        return table_update(Employee)
    else:
        return table_delete(Employee)
