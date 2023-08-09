import os

from flask import Flask, jsonify, render_template
from flask_restful import Api
from flask_jwt_extended import JWTManager
from werkzeug import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from blocklist import BLOCKLIST
from logger import logger
from resources.user import UserRegister, User, UserLogin, UserLogout, TokenRefresh
from resources.strava_auth import StravaAuth
from resources.subject import Subject, SubjectList
from resources.webhooks import Webhook
from resources.activity import SubjectActivities, ActivitiesById, ActivityStreamData

from db import db

frontend = Flask(__name__)
backend = Flask(__name__)

uri = os.environ.get('DATABASE_URL', 'sqlite:///data.db')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
backend.config['SQLALCHEMY_DATABASE_URI'] = uri

backend.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
backend.config['PROPAGATE_EXCEPTIONS'] = True
backend.secret_key = 'YOUR_SECRET_KEY'
api = Api(backend)

jwt = JWTManager(backend)

app = DispatcherMiddleware(frontend, {
    '/api': backend,
})


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return jwt_payload['jti'] in BLOCKLIST


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'description': 'The token has expired',
        'error': 'token_expired'
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(e):
    return jsonify({
        'description': f'{e}',
        'error': 'invalid_token'
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(e):
    return jsonify({
        'description': f'{e}',
        'error': 'authorization_required'
    }), 401


@jwt.needs_fresh_token_loader
def token_not_fresh_callback(jwt_header, jwt_payload):
    return jsonify({
        'description': 'The token is not fresh',
        'error': 'fresh_token_required'
    }), 401


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'description': 'The token has been revoked',
        'error': 'token_revoked'
    }), 401


api.add_resource(UserRegister, '/register')
api.add_resource(User, '/user/<int:user_id>')
api.add_resource(Subject, '/subject/<string:subject_id>')
api.add_resource(SubjectList, '/subjects')
api.add_resource(UserLogin, '/login')
api.add_resource(UserLogout, '/logout')
api.add_resource(TokenRefresh, '/refresh')
api.add_resource(StravaAuth, '/strava_auth/<string:subject_id>')
api.add_resource(Webhook, '/webhooks')

api.add_resource(SubjectActivities, '/subject/<string:subject_id>/activities')
api.add_resource(ActivitiesById, '/activities/<int:strava_activity_id>')

api.add_resource(ActivityStreamData, '/activities/<int:strava_activity_id>/stream')


@frontend.route("/")
def home():
    """Landing page."""
    return render_template(
        "index.jinja2",
        title="Smart Injury Prevention Study",
        subtitle="Thank you for participating!",
        description="Smart Injury Prevention Study",
        template="home-template",
        body="This is a homepage served with Flask.",
    )


logger.info('# # # # # # # # # # # # # # # # # # # #')
logger.info('App started')
logger.info('# # # # # # # # # # # # # # # # # # # #')

if __name__ == '__main__':
    db.init_app(backend)
    # app.run(host='0.0.0.0', debug=True, port=4000)
    run_simple(
        hostname='0.0.0.0',
        port=4000,
        application=app,
        use_reloader=True,
        use_debugger=True,
        use_evalex=True)
