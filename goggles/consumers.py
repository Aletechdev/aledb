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
        machine = text_data_json['machine']
        data_id = text_data_json['data_id']
        self.send(text_data=json.dumps({
            'message': [machine+ale_id, get_experiment_data(machine, ale_id), data_id, name, [ale_id, name, machine, data_id]]
        }, indent=4, sort_keys=True, default=str))
