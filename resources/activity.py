from logger import logger

from flask import jsonify, make_response
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from models.activity import ActivityModel
from models.subject import SubjectModel

from datetime import datetime
import pandas as pd


class ActivitiesById(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('after',
                        type=int,
                        required=False,
                        help="An epoch timestamp to use for filtering activities that have taken place "
                             "after a certain time.")
    parser.add_argument('before',
                        type=int,
                        required=False,
                        help="An epoch timestamp to use for filtering activities that have taken place "
                             "before a certain time.")

    @jwt_required()
    def get(self, strava_activity_id):
        activity = ActivityModel.find_by_strava_id(strava_activity_id)
        if activity:
            return activity.json()
        return {"message": "Activity not found."}, 404

    @jwt_required()
    def put(self, strava_activity_id):
        activity = ActivityModel.find_by_strava_id(strava_activity_id)
        if not activity:
            return {"message": "Activity not found."}, 404
        subject = SubjectModel.find_by_subject_id(activity.subject_id)
        if subject.expires_at < datetime.now().timestamp():
            subject.refresh_tokens()
        if not activity.get_stream_data(access_token=subject.access_token):
            return {"message": "Could not download activity stream data."}, 404
        return activity.json()

    @jwt_required()
    def delete(self, strava_activity_id):
        activity = ActivityModel.find_by_strava_id(strava_activity_id)
        if activity:
            activity.delete_stream_data()
            activity.delete_from_db()
            return {'message': 'Activity deleted'}, 200
        return {'message': 'Activity not found'}, 400


class SubjectActivities(Resource):
    @jwt_required()
    def get(self, subject_id):
        subject = SubjectModel.find_by_subject_id(subject_id)
        if not subject:
            return {'message': f'Subject with subject_id {subject_id} not found.'}, 400
        return {'activities': [activity.json() for activity in ActivityModel.find_by_subject_id(subject_id)]}

    @jwt_required()
    def put(self, subject_id: str):
        args = ActivitiesById.parser.parse_args()
        before = args['before']
        after = args['after']

        subject = SubjectModel.find_by_subject_id(subject_id)
        if not subject:
            return {"message": "Subject not found."}, 400
        df_activities = subject.get_activities(before=before, after=after)
        if df_activities is None:
            return {'message': 'No activities found'}, 404
        logger.info(f'Found {len(df_activities)} activities')
        ActivityModel.get_all(df_activities=df_activities, subject=subject)
        return {'activities': [activity.json() for activity in ActivityModel.find_by_subject_id(subject_id)]}, 200


class ActivityStreamData(Resource):
    @jwt_required()
    def get(self, strava_activity_id):
        logger.info(f'Stream data requested for activity with id: {strava_activity_id}')
        activity = ActivityModel.find_by_strava_id(strava_activity_id)
        if activity:
            if not activity.stream_file_path:
                return {"message": "No stream file for activity."}, 404
            df = pd.read_csv(activity.stream_file_path)
            return make_response(jsonify(df.to_dict()), 200)
        return {"message": "Activity not found."}, 404
