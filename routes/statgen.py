#!/usr/bin/env python
import extensions
from datetime import datetime
from models import Sale, Reservation, Room
from flask import request, Blueprint
from sqlalchemy import and_

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess
stringToDateTime = extensions.stringToDateTime

statgen_blueprint = Blueprint("statgen", __name__, url_prefix='/stat/gen')


@auth.login_required(1)
@statgen_blueprint.route('/sales', methods=['GET'], endpoint='sales')
def sales():
    args = request.args.to_dict()
    startDate = stringToDateTime(args.pop('startdate'))
    endDate = stringToDateTime(args.pop('enddate'))
    sales = Sale.query.filter(and_(Sale.created_at >= startDate, Sale.created_at <= endDate)).all()
    salesroom = 0
    salespax = len(sales)
    salesrev = 0.0
    for sale in sales:
        salesrev += sale.price
        if (sale.reservationid is not None):
            salesroom += 1

    returnData = {'salesroom': salesroom, 'salespax': salespax, 'salesrev': salesrev}

    return dataResultSuccess(returnData, spuriousParameters=args)


@auth.login_required(1)
@statgen_blueprint.route('/revenue', methods=['GET'], endpoint='gen_revenue')
def revenue():
    args = request.args.to_dict()
    startDate = stringToDateTime(args.pop('startdate'))
    endDate = stringToDateTime(args.pop('enddate'))
    timePeriod = endDate - startDate
    sales = Sale.query.filter(and_(Sale.created_at >= startDate, Sale.created_at <= endDate)).all()
    reservations = Reservation.query.filter(and_(Reservation.startdate >= startDate, Reservation.startdate <= endDate)).all()
    roomCount = Room.query.count()
    availableRooms = roomCount * (timePeriod.days + 1)
    for room in reservations:
        roomStartDate = datetime.combine(room.startdate, datetime.min.time())
        roomEndDate = datetime.combine(room.enddate, datetime.min.time())
        if (roomStartDate >= startDate and roomEndDate <= endDate):
            availableRooms -= ((roomEndDate - roomStartDate).days + 1)
            continue
        elif (roomStartDate >= startDate):
            availableRooms -= ((endDate - roomStartDate).days + 1)
            continue
        elif (roomEndDate <= endDate):
            availableRooms -= ((roomEndDate - startDate).days + 1)
            continue
        else:
            availableRooms -= (timePeriod.days + 1)

    revenue = 0.0

    for sale in sales:
        revenue += sale.price
    revadr = 0.0
    revpar = 0.0
    roomrev = 0.0
    if ((timePeriod.days + 1) > 0):
        revadr = revenue / (timePeriod.days + 1)
        if (roomCount > 0):
            roomrev = revenue / roomCount
            revpar = revenue / availableRooms

    returnData = {'revenue': revenue, 'revadr': revadr, 'revpar': revpar, 'roomrev': roomrev}

    return dataResultSuccess(returnData, spuriousParameters=args)
