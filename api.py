#!/usr/bin/env python
from flask import Flask

from extensions import db


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

    from routes import blueprint

    app.register_blueprint(blueprint)

    return app


app = create_app()
app.run(debug=True)
