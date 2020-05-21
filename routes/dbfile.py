import extensions
import os
import sys
import uuid

from flask import request, g, Blueprint, send_from_directory
from models import DBFile
from routes.route_utilities import table_ins, table_get, table_update, table_delete

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess
resultFailure = extensions.resultFailure

dbfile_blueprint = Blueprint("dbfile", __name__, url_prefix="/dbfile")


@dbfile_blueprint.route('', methods=['GET', 'POST', 'PATCH', 'DELETE'], endpoint='dbfile')
@auth.login_required(1)
def endpoint_dbfile():
    if (request.method == 'POST'):
        return table_ins(DBFile)
    elif (request.method == 'GET'):
        return table_get(DBFile)
    elif (request.method == 'PATCH'):
        return table_update(DBFile)
    else:
        return table_delete(DBFile)


@dbfile_blueprint.route('/load', methods=['GET', 'POST'], endpoint='dbfile_load')
@auth.login_required(1)
def load():
    # uploading
    if (request.method == 'POST'):
        uploaded_files = request.files.getlist('file')
        if (not uploaded_files):
            resultFailure("no files recieved.", 400)
        # getting all the parameters
        params = request.args.to_dict()
        masterID = None
        # removing the masterid paramerter if it is there
        if ('masterid' in params):
            masterID = params.pop('masterid')
        # if not, then use the user's guid
        else:
            masterID = g.user.guid

        code = params.pop('code') if 'code' in params else ""
        codeList = code.split(',')
        listLength = len(codeList)
        if (listLength != len(uploaded_files)):
            return resultFailure(msg="Code and file numbers mistmatch.", code=400)
        if (listLength > 1):
            code = codeList

        fileList = []
        for i in range(0, len(uploaded_files)):
            file = uploaded_files[i]
            fileNameList = file.filename.split('.')
            filename = fileNameList[0]
            fileext = fileNameList[1]
            fileItem = DBFile.query.filter_by(masterid=masterID, code=(code[i] if type(code) is list else code)).first()
            if (fileItem is None):
                fileguid = uuid.uuid4()
                fileItem = DBFile(masterid=masterID, guid=fileguid, filename=filename, filetype=fileext, code=(code[i] if type(code) is list else code))
            os.makedirs(os.path.join(sys.path[0] + "/storage/dbfile", str(masterID)), exist_ok=True)
            file.save(os.path.join(sys.path[0] + '/storage/dbfile', str(masterID), str(fileItem.guid) + '.' + fileext))
            db.session.add(fileItem)
            fileList.append(fileItem.to_dict())
        db.session.commit()
        # returning the normal response + getting the non popped parameters into spurious
        return extensions.dataResultSuccess(
            fileList, count=len(fileList), spuriousParameters=list(params.keys()), code=201)

    else:  # Downloading
        arguments = request.args.to_dict()
        dbFileItem = None
        if ('id' in arguments):
            dbFileItem = DBFile.query.filter_by(id=arguments['id']).first()
        elif ('guid' in arguments):
            dbFileItem = DBFile.query.filter_by(guid=arguments['guid']).first()
        elif (('masterid' in arguments) & ('code' in arguments)):
            dbFileItem = DBFile.query.filter_by(masterid=arguments['masterid'], code=arguments['code']).first()
        else:
            resultFailure("no identifier provided, you need to supply ID, GUID, or MasterID & Code.", 400)
        if (dbFileItem is None):
            resultFailure("DBFile not found.", 404)
        return send_from_directory(os.path.join(
            sys.path[0],
            'storage/dbfile',
            str(dbFileItem.masterid)),
            (str(dbFileItem.guid) + '.' + dbFileItem.filetype))
