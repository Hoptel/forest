#!/usr/bin/env python
import extensions
import models
import os
import uuid

from flask import abort, request, g, Blueprint, send_from_directory

auth = extensions.auth
db = extensions.db
dataResultSuccess = extensions.dataResultSuccess
APIUser = models.APIUser
AuthToken = models.AuthToken

dbfile_blueprint = Blueprint("dbfile", __name__, url_prefix="/forest/dbfile")

# TODO maybe make this its own blueprint and separate blueprints
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
        # if not, then use the user's gid
        else:
            masterID = g.user.gid
        fileList = []
        for file in uploaded_files:
            fileNameList = file.filename.split('.')
            filename = fileNameList[0]
            fileext = fileNameList[1]
            fileItem = models.DBFile(masterid=masterID, gid=uuid.uuid4(), filename=filename, filetype=fileext)
            if (masterID is not None):
                os.makedirs(os.path.dirname(__file__) + "/storage/dbfile", str(masterID), exist_ok=True)
                file.save(os.path.join(
                    os.path.dirname(__file__) + '/storage/dbfile', str(masterID), str(fileItem.gid) + '.' + fileext))
            else:
                os.makedirs(os.path.dirname(__file__) + "/storage/dbfile", exist_ok=True)
                file.save(os.path.join(
                    os.path.dirname(__file__) + '/storage/dbfile/', str(fileItem.gid) + '.' + fileext))
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
            dbFileItem = models.DBFile.query.filter_by(id=arguments['id']).first()
        elif ('gid' in arguments):
            dbFileItem = models.DBFile.query.filter_by(gid=arguments['gid']).first()
        elif ('masterid' in arguments & 'code' in arguments):
            dbFileItem = models.DBFile.query.filter_by(masterid=arguments['masterid'], code=arguments['code']).first()
        else:
            abort(400)
        if (dbFileItem is None):
            abort(404)
        return send_from_directory(os.path.join(
            os.path.dirname(__file__),
            'storage/dbfile',
            str(dbFileItem.masterid)),
            (str(dbFileItem.gid) + '.' + dbFileItem.filetype))
