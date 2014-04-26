#!/usr/bin/env python
from reworker.worker import Worker
from juicer.juicer.Juicer import Juicer as j
import juicer.juicer.Parser
import logging

class Juicer(Worker):
    """
    Plugin to run pulp commands. Lets begin with just cart promoting.
    """

    dynamic = ['cart', 'environment']

    def process(self, channel, basic_deliver, properties, body, output):
        juicer.utils.Log.LOG_LEVEL_CURRENT = 0
        corr_id = str(properties.correlation_id)
        dynamic = body.get('dynamic', {})
        if dynamic == {} or \
           dynamic.get('cart', None) == None or \
           dynamic.get('environment', None) == None:
            self.reject(basic_deliver)
            self.app_logger.error("Rejecting message, invalid dynamic data provided")
            self.send(properties.reply_to, corr_id, {'status': 'failed'}, exchange='')
            self.notify(
                'Juicer Failed',
                'Juicer failed. No dynamic keys given. Expected: "cart" and "environment"',
                'failed',
                corr_id)
            return False
        else:
            self.ack(basic_deliver)
            cart = dynamic['cart']
            environment = dynamic['environment']
            self.app_logger.info("Not rejecting. Processing: %s %s" % (cart, environment))

        self.send(properties.reply_to, corr_id, {'status': 'started'}, exchange='')
        self._j_pull(cart)
        self._j_push(cart, environment)
        self.app_logger.info("Pulled and pushed cart")
        self.send(properties.reply_to, corr_id, {'status': 'completed'}, exchange='')

    def _j_pull(self, cart_name):
        """
        Pull down `cart_name` from MongoDB
        """
        self.app_logger.info("Pulling down cart: %s" % cart_name)
        parser = juicer.juicer.Parser.Parser()
        args = parser.parser.parse_args(['cart', 'pull', cart_name])
        result = args.j(args)
        self.app_logger.info("Received cart: %s" % cart_name)

    def _j_push(self, cart_name, environment):
        """
        Push `cart_name` to `environment`
        """
        self.app_logger.info("Pushing cart %s to environment %s" % (cart_name, environment))
        parser = juicer.juicer.Parser.Parser()
        args = parser.parser.parse_args(['cart', 'push', cart_name, '--in', environment])
        result = args.j(args)
        self.app_logger.info("Pushed cart %s to environment %s" % (cart_name, environment))


if __name__ == '__main__':
    logging.getLogger('pika').setLevel(logging.CRITICAL)
    logging.getLogger('pika.channel').setLevel(logging.CRITICAL)

    mq_conf = {
        'server': '127.0.0.1',
        'port': 5672,
        'vhost': '/',
        'user': 'guest',
        'password': 'guest',
    }
    worker = Juicer(mq_conf, '/tmp/logs/')
    worker.run_forever()
