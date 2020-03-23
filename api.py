#!/usr/bin/env python
import threading
import time
import uuid

from flask import Flask
from extensions import db, getCurrenciesFromAPI


currencyThread = None


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'the quick brown dog jumps over the lazy fox'
    # mysql+pymysql://<username>:<password>@<host>/<dbname>'
    # (using sqlite for dev purposes)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    app.config['UPLOAD_FOLDER'] = '/storage/dbfile'

    db.init_app(app)

    import models  # noqa: F401

    with app.app_context():
        db.create_all()
        db.session.commit()

    from routes.route_utilities import verify_token  # noqa: F401
    from routes.user import user_blueprint
    from routes.dbfile import dbfile_blueprint
    from routes.auth import auth_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(dbfile_blueprint)


    currencyThread = threading.Thread(target=putCurrenciesInDB, args=(app,))
    #currencyThread.start()  # enable for testing and production only

    return app


def putCurrenciesInDB(app):
    import models
    while(True):
        with app.app_context():
            currDict = getCurrenciesFromAPI()
            for key, value in currDict.items():
                curr = models.Currency.query.filter_by(code=key).first()
                if (curr is None):
                    curr = models.Currency(code=key, value=value, guid=uuid.uuid4())
                    db.session.add(curr)
                else:
                    curr.value = value
            db.session.commit()
        time.sleep(3600)  # should be 3600 by default


app = create_app()
app.run(debug=True)
currencyThread.join()
