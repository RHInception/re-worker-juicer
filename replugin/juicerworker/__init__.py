#!/usr/bin/env python
from reworker.worker import Worker
import juicer.juicer.Juicer
import juicer.juicer.Parser
import juicer.utils.Log
import juicer.common.Cart
import logging


class JuicerWorker(Worker):
    """
    Plugin to run pulp commands. Lets begin with just cart promoting.
    """

    dynamic = ['cart', 'environment']

    def process(self, channel, basic_deliver, properties, body, output):
        self._channel = channel
        self.output = output
        juicer.utils.Log.LOG_LEVEL_CURRENT = 0
        self.corr_id = str(properties.correlation_id)
        dynamic = body.get('dynamic', {})
        self.reply_to = properties.reply_to

        if (dynamic == {} or
                dynamic.get('cart', None) is None or
                dynamic.get('environment', None) is None):
            self.reject(basic_deliver)
            self.app_logger.error(
                "%s - Rejecting message, invalid dynamic data provided" % (
                    self.corr_id))
            self.send(
                self.reply_to, self.corr_id, {'status': 'failed'}, exchange='')
            self.notify(
                'Juicer Failed',
                ('Juicer failed. No dynamic keys given. '
                    'Expected: "cart" and "environment"'),
                'failed',
                self.corr_id)
            self.send(self.reply_to,
                      self.corr_id,
                      {'status': 'errored',
                       "message": "No dynamic keys given, expected 'cart' and 'environment'"},
                      exchange='')
            return False
        else:
            self.ack(basic_deliver)
            cart = dynamic['cart']
            environment = dynamic['environment']
            output.info(
                "Dynamic cart push parameters: Cart: %s; Environment: %s" % (
                    cart,
                    environment))
            self.app_logger.debug("%s - Not rejecting. Processing: %s %s" % (
                self.corr_id, cart, environment))

        self.send(
            self.reply_to, self.corr_id, {'status': 'started'}, exchange='')
        if self._j_pull(cart):
            self.output.info("Received cart: %s" % (cart))
            if self._j_push(cart, environment):
                self.output.info("Pushed cart %s to environment %s" % (
                    cart, environment))
                self.app_logger.info("%s - Pulled and pushed cart '%s' to %s" %
                                     (self.corr_id, cart, environment))
                self.send(
                    self.reply_to,
                    self.corr_id,
                    {'status': 'completed'},
                    exchange='')
            else:
                self.app_logger.error("%s - Couldn't push cart: %s" % (
                    self.corr_id, cart))
                self.send(
                    self.reply_to,
                    self.corr_id,
                    {'status': 'errored'},
                    exchange='')

    def _j_pull(self, cart_name):
        """
        Pull down `cart_name` from MongoDB
        """
        self.app_logger.info("%s - Pulling down cart: %s" % (
            self.corr_id, cart_name))
        parser = juicer.juicer.Parser.Parser()
        args = parser.parser.parse_args(['-v', 'cart', 'pull', cart_name])
        self.app_logger.debug("%s - Calling juicer api method: %s with: %s" %
                              (self.corr_id,
                               str(args.j),
                               args))

        juiced = juicer.juicer.Juicer.Juicer(args)

        result = juiced.pull(cartname=args.cartname)
        self.app_logger.debug("%s - API result: %s" % (
            self.corr_id, str(result)))
        if result:
            self.app_logger.info("%s - Received cart: %s" % (
                self.corr_id, cart_name))
            return True
        else:
            self.app_logger.error("%s - Couldn't find cart: %s" % (
                self.corr_id, cart_name))
            self.output.error("%s - Couldn't find cart: %s" % (
                self.corr_id, cart_name))
            self.send(
                self.reply_to,
                self.corr_id,
                {'status': 'errored'},
                exchange='')
            return False

    def _j_push(self, cart_name, environment):
        """
        Push `cart_name` to `environment`
        """
        self.app_logger.info("%s - Pushing cart %s to environment %s" % (
            self.corr_id, cart_name, environment))
        parser = juicer.juicer.Parser.Parser()
        args = parser.parser.parse_args([
            '-v', 'cart', 'push', cart_name, '--in', environment])

        try:
            juiced = juicer.juicer.Juicer.Juicer(args)
            cart = juicer.common.Cart.Cart(
                args.cartname, autoload=True, autosync=True)
            juiced.push(
                cart, env=environment, callback=self.on_upload)
            self.app_logger.info("%s - Pushed cart %s to environment %s" % (
                self.corr_id, cart_name, environment))
            return True
        except Exception:
            # Something broke...
            return False

    def on_upload(self, rpm_name):
        """
        Callback for the juicer cart push method when an RPM is uploaded
        """
        self.app_logger.info("%s - Uploaded an RPM: %s" % (
            self.corr_id, rpm_name))
        self.output.info("%s - Uploaded an RPM: %s" % (self.corr_id, rpm_name))

if __name__ == '__main__':  # pragma: no cover
    logging.getLogger('pika').setLevel(logging.CRITICAL)
    logging.getLogger('pika.channel').setLevel(logging.CRITICAL)

    mq_conf = {
        'server': '127.0.0.1',
        'port': 5672,
        'vhost': '/',
        'user': 'guest',
        'password': 'guest',
    }
    worker = JuicerWorker(mq_conf, output_dir='/tmp/logs/')
    worker.run_forever()
