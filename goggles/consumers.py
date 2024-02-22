import json
from channels.generic.websocket import WebsocketConsumer
from .util import get_experiment_data


class GogglesConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        ale_id = text_data_json['db_id']
        name = text_data_json['name']
        self.send(text_data=json.dumps({
            'message': [ale_id, get_experiment_data(ale_id), name]
        }, indent=4, sort_keys=True, default=str))
