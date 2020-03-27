#!/usr/bin/env python
import random
import json
import time
from datetime import datetime

from passlib.hash import pbkdf2_sha512 as sha512
from sqlalchemy_utils import UUIDType
from sqlalchemy import not_
from sqlalchemy.orm.attributes import QueryableAttribute

from extensions import db, dateTimeNow


class BaseModel(db.Model):  # TODO add modified_at and created_at fields (in ISO format)
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64))
    guid = db.Column(UUIDType(binary=False), nullable=False, unique=True)  # set this in the route to uuid.uuid4

    def __init__(self, **kwargs):
        kwargs['_force'] = True
        self._set_columns(**kwargs)

    def _set_columns(self, **kwargs):
        force = kwargs.get('_force')

        readonly = []
        if hasattr(self, '_readonly_fields'):
            readonly = self.readonly_fields
        if hasattr(self, '_hidden_fields'):
            readonly += self._hidden_fields

        readonly += [
            'id',
            'created',
            'updated',
            'modified',
            'created_at',
            'updated_at',
            'modified_at',
        ]

        changes = {}

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()

        for key in columns:
            allowed = True if force or key not in readonly else False
            exists = True if key in kwargs else False
            if allowed and exists:
                val = getattr(self, key)
                if val != kwargs[key]:
                    changes[key] = {'old': val, 'new': kwargs[key]}
                    setattr(self, key, kwargs[key])

        for rel in relationships:
            allowed = True if force or rel not in readonly else False
            exists = True if rel in kwargs else False
            if allowed and exists:
                is_list = self.__mapper__.relationships[rel].uselist
                if is_list:
                    valid_ids = []
                    query = getattr(self, rel)
                    cls = self.__mapper__.relationships[rel].argument()
                    for item in kwargs[rel]:
                        if 'id' in item and query.filter_by(id=item['id']).limit(1).count() == 1:
                            obj = cls.query.filter_by(id=item['id']).first()
                            col_changes = obj.set_columns(**item)
                            if col_changes:
                                col_changes['id'] = str(item['id'])
                                if rel in changes:
                                    changes[rel].append(col_changes)
                                else:
                                    changes.update({rel: [col_changes]})
                            valid_ids.append(str(item['id']))
                        else:
                            col = cls()
                            col_changes = col.set_columns(**item)
                            query.append(col)
                            db.session.flush()
                            if col_changes:
                                col_changes['id'] = str(col.id)
                                if rel in changes:
                                    changes[rel].append(col_changes)
                                else:
                                    changes.update({rel: [col_changes]})
                            valid_ids.append(str(col.id))

                    # delete related rows that were not in kwargs[rel]
                    for item in query.filter(not_(cls.id.in_(valid_ids))).all():
                        col_changes = {
                            'id': str(item.id),
                            'deleted': True,
                        }
                        if rel in changes:
                            changes[rel].append(col_changes)
                        else:
                            changes.update({rel: [col_changes]})
                        db.session.delete(item)

                else:
                    val = getattr(self, rel)
                    if self.__mapper__.relationships[rel].query_class is not None:
                        if val is not None:
                            col_changes = val.set_columns(**kwargs[rel])
                            if col_changes:
                                changes.update({rel: col_changes})
                    else:
                        if val != kwargs[rel]:
                            setattr(self, rel, kwargs[rel])
                            changes[rel] = {'old': val, 'new': kwargs[rel]}

        return changes

    def set_columns(self, **kwargs):
        self._changes = self._set_columns(**kwargs)
        if 'modified' in self.__table__.columns:
            self.modified = dateTimeNow()
        if 'updated' in self.__table__.columns:
            self.updated = dateTimeNow()
        if 'modified_at' in self.__table__.columns:
            self.modified_at = dateTimeNow()
        if 'updated_at' in self.__table__.columns:
            self.updated_at = dateTimeNow()
        return self._changes

    def to_dict(self, show=None, _hide=[], _path=None):
        """Return a dictionary representation of this model."""

        show = show or []

        hidden = self._hidden_fields if hasattr(self, "_hidden_fields") else []
        default = self._default_fields if hasattr(self, "_default_fields") else []
        default.extend(['id', 'modified_at', 'created_at'])

        if not _path:
            _path = self.__tablename__.lower()

            def prepend_path(item):
                item = item.lower()
                if item.split(".", 1)[0] == _path:
                    return item
                if len(item) == 0:
                    return item
                if item[0] != ".":
                    item = ".%s" % item
                item = "%s%s" % (_path, item)
                return item

            _hide[:] = [prepend_path(x) for x in _hide]
            show[:] = [prepend_path(x) for x in show]

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()
        properties = dir(self)

        ret_data = {}

        for key in columns:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            ret_data[key] = getattr(self, key)

        for key in relationships:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                _hide.append(check)
                is_list = self.__mapper__.relationships[key].uselist
                if is_list:
                    items = getattr(self, key)
                    if self.__mapper__.relationships[key].query_class is not None:
                        if hasattr(items, "all"):
                            items = items.all()
                    ret_data[key] = []
                    for item in items:
                        ret_data[key].append(
                            item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        )
                else:
                    if (
                        self.__mapper__.relationships[key].query_class is not None or self.__mapper__.relationships[key].instrument_class
                        is not None
                    ):
                        item = getattr(self, key)
                        if item is not None:
                            ret_data[key] = item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        else:
                            ret_data[key] = None
                    else:
                        ret_data[key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith("_"):
                continue
            if not hasattr(self.__class__, key):
                continue
            attr = getattr(self.__class__, key)
            if not (isinstance(attr, property) or isinstance(attr, QueryableAttribute)):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                val = getattr(self, key)
                if hasattr(val, "to_dict"):
                    ret_data[key] = val.to_dict(
                        show=list(show),
                        _hide=list(_hide),
                        _path=('%s.%s' % (_path, key.lower())),
                    )
                else:
                    ret_data[key] = json.loads(json.dumps(val))

        return ret_data


class AuthToken(db.Model):
    __tablename__ = 'auth_token'
    id = db.Column(db.Integer, primary_key=True)
    token_type = db.Column(db.String(40), default='bearer')
    access_token = db.Column(db.String(64), unique=True, nullable=False)
    refresh_token = db.Column(db.String(64), index=True)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    issued_at = db.Column(db.Integer, nullable=False, default=lambda: int(time.time()))
    expires_in = db.Column(db.Integer, nullable=False, default=86400)
    scope = db.Column(db.Integer, nullable=False, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey('api_user.id', ondelete='CASCADE'))
    user = db.relationship('APIUser')

    def get_expires_in(self):
        return self.expires_in

    def get_expires_at(self):
        return self.issued_at + self.expires_in

    def get_is_expired(self):
        if (self.expires_in == 0):
            return False
        else:
            return self.get_expires_at() <= int(time.time())

    def get_is_invalid(self):
        return self.get_is_expired() or self.revoked

    @staticmethod
    def generate_token():
        return ''.join([str(y) for x in range(64) for y in random.choice(
            '0123456789abcdef')])

    def generate_token_set(self, API_user):
        self.access_token = self.generate_token()
        self.refresh_token = self.generate_token()
        self.revoked = False
        self.issued_at = int(time.time())
        self.user = API_user
        self.user_id = API_user.id
        return True

    def generate_token_access(self):
        self.access_token = self.generate_token()
        self.issued_at = int(time.time())
        return True


class APIUser(BaseModel):
    __tablename__ = 'api_user'
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(256))
    authLevel = db.Column(db.Integer, default=1, nullable=False)
    email = db.Column(db.String(64), unique=True)

    _hidden_fields = ["password_hash"]

    def hash_password(self, password):
        self.password_hash = sha512.hash(password)

    def verify_password(self, password):
        return sha512.verify(password, self.password_hash)


class DBFile(BaseModel):
    __tablename__ = 'dbfile'
    masterid = db.Column(UUIDType(binary=False))  # guid of the item that the file is attached to
    filename = db.Column(db.String(32))
    filetype = db.Column(db.String(8))  # The extension of the file (.jpg, .png)


# value of current currency (vcc), value of convert to currency (vtc), conversion is amount*(vtc/vcc)
class Currency(BaseModel):
    __tablename__ = 'currency'
    value = db.Column(db.Float)
