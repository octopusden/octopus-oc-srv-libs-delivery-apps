from collections import namedtuple
from cdt_queue2.queue_rpc import QueueRPC
from cdt_queue2.queue_application import QueueApplication
from os import getenv

queue_published = ['ping', 'client_availability_update',
                   'upload_to_ftp', 'upload_delivery']
queue_name = 'cdt.dlupload.input'


class UploadWorkerClient(QueueRPC):
    default_queue_name = queue_name
    published = queue_published

    def __init__(self, *args, **argv):
        super(UploadWorkerClient, self).__init__(*args, **argv)

    def basic_args(self, parser=None):
        parser = super(UploadWorkerClient, self).basic_args(parser)
        return parser

    def setup_from_args(self, args=None):
        args = super(UploadWorkerClient, self).setup_from_args(args)

    def send(self, *args, **argv):
        usual = super(UploadWorkerClient, self).send(*args, **argv)
        return usual


class UploadWorkerServer(QueueApplication):
    default_queue_name = queue_name
    published = queue_published

    def client_availability_update(self, client):
        pass

    def upload_to_ftp(self, client):
        pass

    def ping(self):
        pass

    def upload_delivery(self, client):
        pass
