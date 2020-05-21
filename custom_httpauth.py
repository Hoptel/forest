from functools import wraps
from flask import request
from flask_httpauth import HTTPAuth


class CustomHTTPAuth(HTTPAuth):
    def login_required(self, auth_level):
        def actual_decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                auth = self.get_auth()

                # Flask normally handles OPTIONS requests on its own, but in the
                # case it is configured to forward those to the application, we
                # need to ignore authentication headers and let the request through
                # to avoid unwanted interactions with CORS.
                if request.method != 'OPTIONS':  # pragma: no cover
                    password = self.get_auth_password(auth)

                    if not self.authenticate(auth, password, auth_level):
                        # Clear TCP receive buffer of any pending data
                        request.data
                        return self.auth_error_callback()

                return f(*args, **kwargs)
            return decorated
        return actual_decorator


class HTTPTokenAuth(CustomHTTPAuth):
    def __init__(self, scheme='Bearer', realm=None):
        super(HTTPTokenAuth, self).__init__(scheme, realm)

        self.verify_token_callback = None

    def verify_token(self, f):
        self.verify_token_callback = f
        return f

    def authenticate(self, auth, stored_password, auth_level):
        if auth:
            token = auth['token']
        else:
            token = ""
        if self.verify_token_callback:
            return self.verify_token_callback(token, auth_level)
        return False
