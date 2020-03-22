#!/usr/bin/env python
import extensions
import models

from flask import abort, g

auth = extensions.auth
db = extensions.db
AuthToken = models.AuthToken

# This method seems to be called on everything that has [@auth.login_required],
# if this returns true, the method gets executed, otherwise a 401 is returned
@auth.verify_token
def verify_token(token):
    # Getting the token
    userToken = AuthToken.query.filter_by(access_token=token).first()
    if (userToken is None or userToken.get_is_invalid()):
        abort(401)
    g.user = userToken.user
    g.authLevel = userToken.scope
    return True
