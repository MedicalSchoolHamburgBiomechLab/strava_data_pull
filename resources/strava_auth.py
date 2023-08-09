from flask_restful import Resource, reqparse
from flask import make_response, render_template, redirect, url_for
import requests
from constants import *
from logger import logger

from models.subject import SubjectModel


class StravaAuth(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('code', type=str, location='args')
    parser.add_argument('scope', type=str, location='args')

    def get(self, subject_id: str):
        if not (subject_id.startswith('S') & (len(subject_id) == 4)):
            logger.error(f'Unknown subject {subject_id}.')
            return redirect("https://www.smart-injury.de", code=302)
        logger.info(f'Subject {subject_id} gave authorization.')

        parser_data = StravaAuth.parser.parse_args()
        logger.debug(parser_data)
        subject = SubjectModel.find_by_subject_id(subject_id)
        if subject:
            logger.warning(f'Subject {subject_id} already in database. Try adding manually.')
            return redirect("https://www.smart-injury.de", code=302)

        if parser_data['code']:
            athlete_data = self.get_tokens(code=parser_data['code'])
            logger.debug(f'athlete_data: {athlete_data}.')
            # todo: check what happens if code is invalid!
            new_subject = SubjectModel(subject_id, athlete_data)
            new_subject.save_to_db()
            logger.info(f'Subject {subject_id} added to db.')
        return redirect("https://www.smart-injury.de", code=302)

    def get_tokens(self, code):
        # Make Strava auth API call with client_id, client_secret and code
        response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
        if response.status_code == 200:
            return response.json()

