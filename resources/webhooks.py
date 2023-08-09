import threading
from flask_restful import Resource, reqparse

from logger import logger
from models.activity import ActivityModel


class Webhook(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('hub.mode',
                            type=str,
                            required=True,
                            location='args',
                            help="TBA")
        parser.add_argument('hub.challenge',
                            type=str,
                            required=True,
                            location='args',
                            help="TBA")
        parser.add_argument('hub.verify_token',
                            type=str,
                            required=True,
                            location='args',
                            help="TBA")
        data = parser.parse_args()
        logger.info("# # # # # # # # # # # # # # # # # # # # #")
        logger.info("Received webhook subscription validation request")
        logger.info(data)
        logger.info("# # # # # # # # # # # # # # # # # # # # #")

        return {"hub.challenge": f'{data["hub.challenge"]}'}, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('aspect_type',
                            type=str,
                            required=True,
                            help="TBA")
        parser.add_argument('object_id',
                            type=int,
                            required=True,
                            help="TBA")
        parser.add_argument('object_type',
                            type=str,
                            required=True,
                            help="TBA")
        parser.add_argument('updates',
                            type=dict,
                            required=True,
                            help="TBA")
        parser.add_argument('owner_id',
                            type=int,
                            required=True,
                            help="TBA")
        parser.add_argument('subscription_id',
                            type=int,
                            required=True,
                            help="TBA")
        parser.add_argument('event_time',
                            type=int,
                            required=True,
                            help="TBA")

        data = parser.parse_args()

        logger.info("# # # # # # # # # # # # # # # # # # # # #")
        logger.info("Received webhook event")
        logger.info(data)
        logger.info("# # # # # # # # # # # # # # # # # # # # #")
        try:
            ActivityModel.from_webhook_event(data)
        except Exception as err:
            logger.exception(err)
        return 200
