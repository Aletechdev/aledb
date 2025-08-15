import json
import time
import logging
from channels.generic.websocket import WebsocketConsumer
from .util import get_experiment_data

logger = logging.getLogger(__name__)

class GogglesConsumer(WebsocketConsumer):
    def connect(self):
        try:
            logger.info("GogglesConsumer: WebSocket connection established.")
            self.accept()
        except Exception as e:
            logger.exception("Error during WebSocket connect")
            raise

    def disconnect(self, close_code):
        logger.info(f"GogglesConsumer: WebSocket disconnected with code {close_code}")

    def receive(self, text_data):
        start_time = time.time()
        try:
            logger.debug(f"Raw WebSocket message received: {text_data}")
            text_data_json = json.loads(text_data)
            db_id = text_data_json['db_id']
            name = text_data_json['name']
            machine = text_data_json['machine']
            data_id = text_data_json['data_id']
            sample_name = text_data_json['sample_name']

            logger.info(f"Parsed WebSocket message - machine={machine}, db_id={db_id}, sample={sample_name}")

            logger.info("Calling get_experiment_data()...")
            exp_start = time.time()
            exp_data = get_experiment_data(machine, db_id)
            logger.info(f"get_experiment_data() completed in {time.time() - exp_start:.2f} seconds. "
                        f"OD count={len(exp_data[0])}, GR count={len(exp_data[1])}, Temp count={len(exp_data[2])}")

            # AFTER (aligned with the front-end)
            payload = {
              "message": [
              f"{machine}{db_id}",
              [exp_data[0], exp_data[1], exp_data[2]],
              f"{machine} - {sample_name}",
              data_id,
              sample_name,
             ]
            }
            self.send(text_data=json.dumps(payload, default=str))
            logger.info(f"Sent WebSocket response in {time.time() - start_time:.2f} seconds")

        except Exception:
            logger.exception("Error processing WebSocket message")
            raise

