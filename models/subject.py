from db import db
import requests
from constants import *
from datetime import datetime
import pandas as pd

from logger import logger


class SubjectModel(db.Model):
    __tablename__ = 'subject'

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.String(4), unique=True, nullable=False)
    strava_id = db.Column(db.Integer)
    sex = db.Column(db.String(2))
    access_token = db.Column(db.String(80))
    refresh_token = db.Column(db.String(80))
    expires_at = db.Column(db.Integer)

    def __init__(self, subject_id, data):
        self.strava_id = data['athlete']['id']
        self.sex = data['athlete']['sex']
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.expires_at = data['expires_at']
        self.subject_id = subject_id

    def json(self):
        return {
            'id': self.id,
            'strava_id': self.strava_id,
            'subject_id': self.subject_id,
            'sex': self.sex,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at,
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
        logger.info(f'Subject {self.subject_id} deleted.')

    def get_new_tokens(self):
        # Make Strava auth API call with client_id, client_secret and code
        response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        data = response.json()
        return data['access_token'], data['refresh_token'], data['expires_at']

    def refresh_tokens(self):
        # Make Strava auth API call with client_id, client_secret and code
        response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        data = response.json()
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.expires_at = data['expires_at']
        self.save_to_db()
        return data['access_token']

    def get_activities(self, before: int = None, after: int = None):
        if self.expires_at < datetime.now().timestamp():
            self.refresh_tokens()
        if not after:
            after = int(datetime(year=2021,
                                 month=10,
                                 day=22,
                                 ).timestamp())
        if not before:
            before = int(datetime(year=2023,
                                  month=1,
                                  day=31,
                                  ).timestamp())

        # Create the dataframe ready for the API call to store your activity data
        activities = pd.DataFrame(
            columns=[
                "id",
                "athlete_id",
                "distance",
                "moving_time",
                "total_elevation_gain",
                "type",
                "start_date",
                "start_date_local"
            ]
        )

        url = "https://www.strava.com/api/v3/athlete/activities"
        # Loop through all activities
        page = 1

        logger.info(f'Activites request for subject {self.subject_id}')
        while True:
            logger.info(f'Page {page}')
            # get page of activities from Strava
            params = {'after': after,
                      'before': before,
                      'per_page': 200,
                      'page': str(page),
                      }
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            r = requests.get(url, params=params, headers=headers)
            if r.status_code != 200:
                logger.warning(f'Activites request returned {r.status_code}: {r.json}')
                return None
            r = r.json()
            # todo: handle "Record Not Found"
            # if no results then exit loop
            if not r:
                break
            # otherwise add new data to dataframe
            for x in range(len(r)):
                if 'run' not in str(r[x]['type']).lower():
                    continue
                activities.loc[x + (page - 1) * 200, 'id'] = r[x]['id']
                activities.loc[x + (page - 1) * 200, 'athlete_id'] = r[x]['athlete']['id']
                activities.loc[x + (page - 1) * 200, 'distance'] = r[x]['distance']
                activities.loc[x + (page - 1) * 200, 'moving_time'] = r[x]['moving_time']
                activities.loc[x + (page - 1) * 200, 'total_elevation_gain'] = r[x]['total_elevation_gain']
                activities.loc[x + (page - 1) * 200, 'type'] = r[x]['type']
                activities.loc[x + (page - 1) * 200, 'start_date'] = r[x]['start_date']
                activities.loc[x + (page - 1) * 200, 'start_date_local'] = r[x]['start_date_local']
            # increment page
            page += 1
        return activities

    def get_activity(self, strava_activity_id):
        if self.expires_at < datetime.now().timestamp():
            self.refresh_tokens()
        url = f'https://www.strava.com/api/v3/activities/{strava_activity_id}'
        params = {'access_token': self.access_token,
                  'include_all_efforts': 'false',
                  }
        r = requests.get(url, params=params)
        if r.status_code != 200:
            return None
        r = r.json()
        activity = {
            "id": strava_activity_id,
            "athlete_id": r['athlete']['id'],
            "distance": r['distance'],
            "moving_time": r['moving_time'],
            "total_elevation_gain": r['total_elevation_gain'],
            "type": r['type'],
            "start_date": r['start_date'],
            "start_date_local": r['start_date_local']
        }
        return pd.DataFrame(activity, index=[0])

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_strava_id(cls, strava_id):
        return cls.query.filter_by(strava_id=strava_id).first()

    @classmethod
    def find_by_subject_id(cls, subject_id):
        return cls.query.filter_by(subject_id=subject_id).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()
