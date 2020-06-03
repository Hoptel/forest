#!/usr/bin/env python
import extensions
from models import Sale, Reservation, Room
from flask import request, Blueprint
from sqlalchemy import and_

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess
stringToDateTime = extensions.stringToDateTime

statgen_blueprint = Blueprint("reservat", __name__, url_prefix='/stat/gen')


@auth.login_required(1)
@statgen_blueprint.route('/sales', methods=['GET'])
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
@statgen_blueprint.route('/revenue', methods=['GET'])
def revenue():
    args = request.args.to_dict()
    startDate = stringToDateTime(args.pop('startdate'))
    endDate = stringToDateTime(args.pop('enddate'))
    timePeriod = endDate - startDate
    sales = Sale.query.filter(and_(Sale.created_at >= startDate, Sale.created_at <= endDate)).all()
    reservations = Reservation.query.filter(and_(Reservation.startdate >= startDate, Reservation.startdate <= endDate)).all()
    roomCount = Room.query.count()
    availableRooms = roomCount * timePeriod.days
    for room in reservations:
        if (room.startDate >= startDate and room.endDate <= endDate):
            availableRooms -= (room.endDate - room.startDate)
            continue
        elif (room.startDate >= startDate):
            availableRooms -= (endDate - room.startDate)
            continue
        elif (room.endDate <= endDate):
            availableRooms -= (room.endDate - startDate)
            continue
        else:
            availableRooms -= timePeriod

    nettotal = 0.0

    for sale in sales:
        nettotal += sale.price

    revadr = nettotal / timePeriod.days
    revpar = nettotal / availableRooms
    roomrev = nettotal / roomCount

    returnData = {'nettotal': nettotal, 'revadr': revadr, 'revpar': revpar, 'roomrev': roomrev}

    return dataResultSuccess(returnData, spuriousParameters=args)
