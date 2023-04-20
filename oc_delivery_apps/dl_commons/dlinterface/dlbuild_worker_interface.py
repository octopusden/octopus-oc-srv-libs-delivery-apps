from cdt_queue2.queue_rpc import QueueRPC
from cdt_queue2.queue_application import QueueApplication

queue_name = "cdt.dlbuild.input"
queue_published = ["ping", "build_delivery"]


class DLBuildQueueClient(QueueRPC):
    default_queue_name = queue_name
    published = queue_published

    def __init__(self, *args, **kvargs):
        super(DLBuildQueueClient, self).__init__(*args, **kvargs)


class DLBuildQueueServer(QueueApplication):
    default_queue_name = queue_name
    published = queue_published

    def build_delivery(self, delivery_tag):
        pass

    def ping(self):
        pass
