from hmac import compare_digest
from logger import logger

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from flask_restful import Resource, reqparse

from blocklist import BLOCKLIST
from models.user import UserModel

_user_parser = reqparse.RequestParser()
_user_parser.add_argument('username',
                          type=str,
                          required=True,
                          help="This field cannot be left blank"
                          )
_user_parser.add_argument('password',
                          type=str,
                          required=True,
                          help="This field cannot be left blank"
                          )


class UserRegister(Resource):
    def post(self):
        data = _user_parser.parse_args()
        if UserModel.find_by_username(data['username']):
            return {"message": "User already exists."}, 400
        # todo: use werkzeugs "generate_password_hash" and "check_password_hash" to properly save passwords
        user = UserModel(**data)
        user.save_to_db()
        logger.info(f'User {user.username} registered.')
        return {"message": "User created successfully."}, 201


class User(Resource):
    @classmethod
    @jwt_required()
    def get(cls, user_id):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': 'User not found'}, 404
        return user.json()

    @classmethod
    @jwt_required()
    def delete(cls, user_id):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': 'User not found'}, 404
        user.delete_from_db()
        logger.info(f'User {user.username} deleted from db.')
        return {'message': 'User deleted'}


class UserLogin(Resource):
    @classmethod
    def post(cls):
        data = _user_parser.parse_args()
        user = UserModel.find_by_username(data['username'])
        if user and compare_digest(data['password'], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)
            logger.info(f'User {user.username} logged in.')
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
            }, 202
        return {'message': 'Invalid credentials'}, 401


class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        BLOCKLIST.add(jti)
        logger.info(f'User logged out.')
        return {'message': 'Successfully logged out.'}, 200


class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}, 200