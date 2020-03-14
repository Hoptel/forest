#!/usr/bin/env python
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify

import requests
import json

db = SQLAlchemy()
auth = HTTPTokenAuth()

def dataResultSuccess(data, msg="", spuriousParameters=[], count=1, code=200):
    return (jsonify({"success": True, "msg": msg, "spurious-parameters": spuriousParameters, "data": data, "count": count}), code)


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
