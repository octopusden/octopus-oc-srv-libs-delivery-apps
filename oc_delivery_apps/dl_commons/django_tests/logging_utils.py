import logging


class MockHandler(logging.NullHandler):
    """ Context manager for storing messages passed to specific logger. 
    These messages are available in logged_messages attribute """

    def __init__(self, logger):
        """ 
        :param logger: logger whom messages will be remembered """
        super(MockHandler, self).__init__()
        self.logged_messages=[]
        self.logger=logger

    def __enter__(self):
        self.logger.addHandler(self)
        return self

    def __exit__(self, *args):
        self.logger.removeHandler(self)
    
    def handle(self, record):
        self.logged_messages.append(record)
        return super(MockHandler, self).handle(record)
