import os
import logging
from functools import wraps
from logging import Formatter
from logging.handlers import RotatingFileHandler
from flask import Flask, session, redirect, url_for
# from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
# from flask_talisman import Talisman

APP = None
WORKER_ID = 0
LOG = logging

USER_DATA = {
    "gAAAAABhOP8DT2sdCXCyAaOhTKFkl-fAH53yqr0A2OtQf_TDtjFjXTN2QOZny2e_7-6Oo-kL0nki8NvaLgsWADlhWHAicHcfVw==": "gAAAAABhOP8tz6pbRhs8WfllNZU2HNzaheB1xdrXBO1P-o-_JACPEG5SG6GkfzIPcVtl4JEo_1CEZYTxb_p5b4sAYpoqijQ2tw=="
}


class User(object):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "User(id='%s')" % self.id


def verify(username, password):
    if not (username and password):
        return False
    if USER_DATA.get(username) == password:
        return User(id=123)


def identity(payload):
    user_id = payload['identity']
    return {"user_id": user_id}



def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        username = session.get('user')
        if bool(username):
            return test(*args, **kwargs)
        else:
            return redirect(url_for('view.login'))
    return wrap


def uwsgi_friendly_setup(app):
    global WORKER_ID

    try:
        import uwsgi
        WORKER_ID = uwsgi.worker_id()
    except ImportError:
        pass
        # During development on local machine, we may use `flask run` command
        # in this case, uwsgi package won't be available and it will throw error


def init_routes(app):
    from .views import bp
    app.register_blueprint(bp)



def create_app():
    global APP

    if APP is not None:
        return APP

    APP = Flask(__name__)
    APP.debug = True

    uwsgi_friendly_setup(APP)
    APP.wsgi_app = ProxyFix(APP.wsgi_app, x_for=1, x_host=1)

    try:
        # api.init_app(APP)
        init_routes(APP)
        ROOT_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..'))
        UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'uploads')
        BASE_IMGS_FOLDER= os.path.join(ROOT_DIR, 'imgsfolder')
        APP.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        APP.config['BASE_IMGS_FOLDER']=BASE_IMGS_FOLDER
        APP.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
        ALLOWED_EXTENSIONS = {'txt', 'pdf'}
        APP.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

        # routes.init_routes(APP)
        # seeds.init_seeds(APP)
        # services.init_app(APP)
    except Exception as e:
        LOG.error('An error happened during initializing app components: %s', e)
        raise

    APP.logger.info('App Initialization is finished successfully')
    return APP
