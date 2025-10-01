from azure.storage.queue import QueueClient

class QueueService:
    def __init__(self, connection_string: str, queue_name: str):
        self.queue = QueueClient.from_connection_string(connection_string, queue_name)

    def create_queue(self):
        self.queue.create_queue()

    def delete_queue(self):
        self.queue.delete_queue()

    def send_message(self, message: str):
        self.queue.send_message(message)

    def receive_message(self):
        return self.queue.receive_message()

    def delete_message(self):
        return self.queue.delete_message()