import json
from channels.generic.websocket import WebsocketConsumer
from .util import get_experiment_data


class GogglesConsumer(WebsocketConsumer):
    def connect(self):
        try:
            # Connection logic
            self.accept()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            db_id = text_data_json['db_id']
            name = text_data_json['name']
            machine = text_data_json['machine']
            data_id = text_data_json['data_id']
            sample_name = text_data_json['sample_name']
            self.send(text_data=json.dumps({
                'message': [machine+db_id, get_experiment_data(machine, db_id), sample_name, data_id, [db_id, name, machine, data_id, sample_name]]
            }, indent=4, sort_keys=True, default=str))
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

