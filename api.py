#!/usr/bin/env python
from flask import Flask
from extensions import db, alembic


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

    alembic.init_app(app)
    db.init_app(app)

    import models  # noqa: F401

    with app.app_context():
        db.create_all()
        db.session.commit()
        alembic.revision('making changes')
        alembic.upgrade()

    from routes.route_utilities import verify_token  # noqa: F401
    from routes.user import user_blueprint
    from routes.dbfile import dbfile_blueprint
    from routes.auth import auth_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(dbfile_blueprint)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

currencyThread.join()
