from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from logger import logger
from models.subject import SubjectModel


class Subject(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('strava_id',
                        type=str,
                        required=True,
                        help="This field cannot be left blank")
    parser.add_argument('sex',
                        type=str,
                        required=True,
                        help="Every subject needs a sex")
    parser.add_argument('access_token',
                        type=str,
                        required=True,
                        help="Every subject needs an access_token")
    parser.add_argument('refresh_token',
                        type=str,
                        required=True,
                        help="Every subject needs a refresh_token")
    parser.add_argument('expires_at',
                        type=int,
                        required=True,
                        help="Expiry date required")

    @jwt_required()
    def get(self, subject_id: str):
        subject = SubjectModel.find_by_subject_id(subject_id)
        if subject:
            logger.info(f'Subject requested: {subject.json()}')
            return subject.json()
        return {"message": "Item not found."}, 404

    @jwt_required()
    def post(self, subject_id: str):
        if SubjectModel.find_by_subject_id(subject_id):
            return {'message': f'A subject with id {subject_id} already exists'}, 400

        data = Subject.parser.parse_args()
        data_reformat = {
            'athlete': {
                'id': data['strava_id'],
                'sex': data['sex']
            },
            'access_token': data['access_token'],
            'refresh_token': data['refresh_token'],
            'expires_at': data['expires_at'],
        }
        subject = SubjectModel(subject_id=subject_id, data=data_reformat)
        try:
            subject.save_to_db()
        except Exception as err:
            logger.exception(err)
            return {"message": "An error occurred inserting the subject."}, 500

        return subject.json(), 201

    @jwt_required()
    def put(self, subject_id: str):
        subject = SubjectModel.find_by_subject_id(subject_id)
        if not subject:
            return {'message': f'Subject with subject_id {subject_id} not found.'}, 400

        access_token, refresh_token, expires_at = subject.get_new_tokens()
        subject.access_token = access_token
        subject.refresh_token = refresh_token
        subject.expires_at = expires_at

        try:
            subject.save_to_db()
        except Exception as err:
            return {"message": "An error occurred inserting the subject."}, 500

        return subject.json(), 201

    @jwt_required()
    def delete(self, subject_id: str):
        subject = SubjectModel.find_by_subject_id(subject_id)
        if not subject:
            return {'message': f'Subject {subject_id} not found'}, 404
        subject.delete_from_db()
        return {'message': f'Subject {subject_id} deleted'}


class SubjectList(Resource):
    @jwt_required()
    def get(self):
        return {'subjects': [x.json() for x in SubjectModel.find_all()]}