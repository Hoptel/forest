#!/usr/bin/env python
import requests
import json

from datetime import datetime
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify, make_response


db = SQLAlchemy()
auth = HTTPTokenAuth()


def dataResultSuccess(data, msg="", spuriousParameters=[], count=1, code=200):
    return make_response((jsonify({"success": True, "msg": msg, "spuriousparameters": spuriousParameters, "data": data, "count": count}), code))


def getCurrenciesFromAPI():
    # call the currency API
    response = requests.get('http://openexchangerates.org/api/latest.json?app_id=79cbcd6eacd64256945500440eabcff9')
    # remove the b'' and \n     in the string (after converting the response to a string)
    responseString = str(response.content).replace(r"\n", "")
    responseString = responseString.replace(r"    ", "")
    responseString = responseString.lstrip('b')
    responseString = responseString.strip('\'')
    # get only the rates object (since we don't care about much else in the response)
    responseJson = json.loads(responseString)['rates']
    return responseJson


# TODO parse a json formatted query directly instead of giving an error
def queryToJson(queryParam):
    newQueryParam = "{"
    queryParam = queryParam.replace(' ', '')  # Remove all whitespaces
    queryList = queryParam.split(',')  # split the string into queries
    for part in queryList:
        subParts = part.split(':')  # further split things into key, value pairs
        newQueryParam += '"' + subParts[0] + '":"' + subParts[1] + '",'  # reconstruct the key value pairs in the new parameter
    newQueryParam = newQueryParam[:-1]  # remove the last trailing comma
    newQueryParam += '}'  # finish by adding the closing bracket
    return json.loads(newQueryParam)


def timeNow():
    return datetime.utcnow().replace(microsecond=0).isoformat()
