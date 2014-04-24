#!/usr/bin/env python
from reworker.worker import Worker
from juicer.juicer.Juicer import Juicer as j


class Juicer(Worker):
    """
    Plugin to run pulp commands. Lets begin with just cart promoting.
    """

    def process(self, channel, basic_deliver, properties, body, output):
        self.ack(basic_deliver)
        corr_id = str(properties.correlation_id)
        self.send('release.step', corr_id, {'status': 'started'})
        print body


    def _j_pull(self, cart_name):
        """
        Pull down `cart_name` from MongoDB
        """
        pass

    def _j_push(self, cart_name, environment):
        """
        Push `cart_name` to `environment`
        """
        pass



if __name__ == '__main__':
    mq_conf = {
        'server': '127.0.0.1',
        'port': 5672,
        'vhost': '/',
        'user': 'guest',
        'password': 'guest',
    }
    worker = ShellExec(mq_conf, 'worker queue', '/tmp/logs/')
    worker.run_forever()
