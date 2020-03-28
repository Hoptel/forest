#!/usr/bin/env python
import extensions
import os
import uuid

from flask import abort, request, g, Blueprint, send_from_directory
from models import DBFile
from extensions import table_ins, table_get, table_update, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess

dbfile_blueprint = Blueprint("dbfile", __name__, url_prefix="/forest/dbfile")


@dbfile_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@auth.login_required
def endpoint_dbfile():
    if (request.method == 'POST'):
        return table_ins(DBFile)
    elif (request.method == 'GET'):
        return table_get(DBFile)
    elif (request.method == 'PATCH'):
        return table_update(DBFile)
    else:
        return table_delete(DBFile)


@dbfile_blueprint.route('/dbfile/load', methods=['GET', 'POST'])
@auth.login_required
def load():
    # uploading
    if (request.method == 'POST'):
        uploaded_files = request.files.getlist('file')
        # getting all the parameters
        params = request.args.to_dict()
        masterID = None
        # removing the masterid paramerter if it is there
        if ('masterid' in params):
            masterID = params.pop('masterid')
        # if not, then use the user's guid
        else:
            masterID = g.user.guid
        fileList = []
        for file in uploaded_files:
            fileNameList = file.filename.split('.')
            filename = fileNameList[0]
            fileext = fileNameList[1]
            fileItem = DBFile(masterid=masterID, guid=uuid.uuid4(), filename=filename, filetype=fileext)
            if (masterID is not None):
                os.makedirs(os.path.dirname(__file__) + "/storage/dbfile", str(masterID), exist_ok=True)
                file.save(os.path.join(
                    os.path.dirname(__file__) + '/storage/dbfile', str(masterID), str(fileItem.guid) + '.' + fileext))
            else:
                os.makedirs(os.path.dirname(__file__) + "/storage/dbfile", exist_ok=True)
                file.save(os.path.join(
                    os.path.dirname(__file__) + '/storage/dbfile/', str(fileItem.guid) + '.' + fileext))
            db.session.add(fileItem)
            fileList.append(file.filename)
        db.session.commit()
        # returning the normal response + getting the non popped parameters into spurious
        return extensions.dataResultSuccess(
            fileList, count=len(uploaded_files), spuriousParameters=list(params.keys()), code=201)
    else:
        arguments = request.args.to_dict()
        dbFileItem = None
        if ('id' in arguments):
            dbFileItem = DBFile.query.filter_by(id=arguments['id']).first()
        elif ('guid' in arguments):
            dbFileItem = DBFile.query.filter_by(guid=arguments['guid']).first()
        elif ('masterid' in arguments & 'code' in arguments):
            dbFileItem = DBFile.query.filter_by(masterid=arguments['masterid'], code=arguments['code']).first()
        else:
            abort(400)
        if (dbFileItem is None):
            abort(404)
        return send_from_directory(os.path.join(
            os.path.dirname(__file__),
            'storage/dbfile',
            str(dbFileItem.masterid)),
            (str(dbFileItem.guid) + '.' + dbFileItem.filetype))