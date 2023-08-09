import os

import pandas as pd
import requests

from db import db
from models.subject import SubjectModel

from logger import logger


class ActivityModel(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.String, db.ForeignKey('subject.subject_id'))

    strava_activity_id = db.Column(db.BigInteger, unique=True, nullable=False)
    strava_athlete_id = db.Column(db.BigInteger)

    distance = db.Column(db.Float(precision=1))
    moving_time = db.Column(db.BigInteger)
    total_elevation_gain = db.Column(db.Float(precision=1))
    activity_type = db.Column(db.String(40))
    start_date = db.Column(db.String(40))
    start_date_local = db.Column(db.String(40))

    stream_file_path = db.Column(db.String(120))

    subject = db.relationship('SubjectModel')

    def __init__(self, subject_id: str, activity_data: pd.DataFrame):
        self.strava_activity_id = int(activity_data['id'])
        self.strava_athlete_id = int(activity_data['athlete_id'])

        self.distance = float(activity_data['distance'])
        self.moving_time = int(activity_data['moving_time'])
        self.total_elevation_gain = float(activity_data['total_elevation_gain'])
        self.activity_type = str(activity_data['type'])
        self.start_date = str(activity_data['start_date'])
        self.start_date_local = str(activity_data['start_date_local'])

        self.stream_file_path = ""

        self.subject_id = str(subject_id)

    def json(self):
        return {
            'id': self.id,
            'strava_activity_id': self.strava_activity_id,
            'strava_athlete_id': self.strava_athlete_id,
            'subject_id': self.subject_id,
            'distance': self.distance,
            'moving_time': self.moving_time,
            'total_elevation_gain': self.total_elevation_gain,
            'activity_type': self.activity_type,
            'start_date': self.start_date,
            'start_date_local': self.start_date_local,
            'stream_file_path': self.stream_file_path,
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_strava_id(cls, strava_activity_id):
        return cls.query.filter_by(strava_activity_id=strava_activity_id).first()

    @classmethod
    def find_by_subject_id(cls, subject_id):
        return cls.query.filter_by(subject_id=subject_id).all()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def get_stream_data(self, access_token):
        logger.info(f'Requesting stream data for activity {self.strava_activity_id}')
        # possible streams: https://developers.strava.com/docs/reference/#api-models-StreamSet
        url = f'https://www.strava.com/api/v3/activities/{self.strava_activity_id}/streams'
        params = {'key_by_type': 'true',
                  'keys': 'time,distance,velocity_smooth,altitude,latlng,temp,cadence,grade_smooth,heartrate', }
        r = requests.get(url,
                         params=params,
                         headers={'Authorization': f'Bearer {access_token}'})

        if r.status_code != 200:
            # stream data does not exist (manually added activity)
            logger.error(f'Requesting stream data for activity {self.strava_activity_id} failed')
            # todo: add bool parameter "manual" to model like in the original strava data structure
            return False
        r = r.json()
        out = dict()
        for key, value in r.items():
            out[key] = value['data']
        df = pd.DataFrame(out)
        self.stream_file_path = f'/home/sip/data/activities/{self.strava_activity_id}.csv'
        df.to_csv(self.stream_file_path)
        self.save_to_db()
        return True

    def delete_stream_data(self):
        if os.path.exists(self.stream_file_path):
            os.remove(self.stream_file_path)
        return

    @classmethod
    def from_webhook_event(cls, event_data: dict):
        # Create an activity which has recently been uploaded and indicated through a webhook event to the API
        # see: https://developers.strava.com/docs/webhooks/ for example data and handling
        # Check if the webhook event is of create-activity type
        if event_data['object_type'] != 'activity':
            logger.warning("event_data['object_type'] != 'activity'")
            return
        # Find the subject of this activity
        subject = SubjectModel.find_by_strava_id(event_data['owner_id'])
        if not subject:
            logger.warning(f'subject with strava athlete id {event_data["owner_id"]} not found')
            return

        if event_data['aspect_type'] == 'create':
            # Get the activity from strava
            new_activity = subject.get_activity(event_data['object_id'])
            if new_activity is None:
                logger.warning(f'Could not retrieve activity. Object ID: {event_data["object_id"]}')
                return
            activity = cls(subject_id=subject.subject_id,
                           activity_data=new_activity.loc[0])
            if 'run' not in str(activity.activity_type).lower():
                logger.warning(f'activity_type != running')
                return
            logger.info(f'saving to db {activity.json()}')
            activity.save_to_db()
            activity.get_stream_data(access_token=subject.access_token)

        elif event_data['aspect_type'] == 'delete':
            delete_activity = cls.find_by_strava_id(event_data["object_id"])
            if not delete_activity:
                # todo: will happen every time a non-running activity is deleted
                logger.warning(f'activity with strava activity id {event_data["object_id"]} not found')
                return
            logger.info(f'deleting from db {delete_activity.json()}')
            delete_activity.delete_stream_data()
            delete_activity.delete_from_db()
        # todo: implement update!

    @classmethod
    def get_all(cls, df_activities: pd.DataFrame, subject: SubjectModel):
        for row, df_activity in df_activities.iterrows():
            new_activity = ActivityModel.find_by_strava_id(strava_activity_id=df_activity['id'])
            if new_activity:
                # db entry already exists. check if the stream data is also present
                if new_activity.stream_file_path:
                    # if so. do nothing
                    logger.info(f'Activity {new_activity.strava_activity_id} already exists. Not adding.')
                    continue
                logger.info(f'Getting data stream for activity {new_activity.strava_activity_id}')
                new_activity.get_stream_data(subject.access_token)
                continue
            activity = ActivityModel(subject_id=str(subject.subject_id),
                                     activity_data=df_activity)
            logger.info(f'Adding activity {activity.strava_activity_id} to db')
            activity.save_to_db()
            # activity.get_stream_data(subject.access_token)

