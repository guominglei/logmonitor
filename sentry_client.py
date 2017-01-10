# -*- coding:utf-8 -*-

import raven
from raven.transport import GeventedHTTPTransport
import gevent


def send_msg(sender, msg, tags):

    sender.captureMessage(msg, tags=tags)


def test():

    dns = ("http://e69dc261db4d4158873d2669308a46c8:"
           "f8f5d9435fb44f5d91b9f06ddb43fd25@192.168.249.138:9000/4")

    client = raven.Client(dns, transport=GeventedHTTPTransport)

    msg = "gevent client t"

    tags = {"test": "geventclient"}

    #workers = []
    worker = gevent.spawn(send_msg, client, msg, tags)

    # workers.append(worker)
    #
    # for wk in workers:
    #     wk.join()


if __name__ == "__main__":

    test()

