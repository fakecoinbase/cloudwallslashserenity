import capnp
import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream

capnp.remove_import_hook()
fh_capnp = capnp.load('../../../../serenity-fh/capnp/serenity-fh.capnp')

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5556")
socket.setsockopt_string(zmq.SUBSCRIBE, "")
stream = ZMQStream(socket)


def on_message(msgs):
    msg = fh_capnp.TradeMessage.from_bytes(msgs[0])
    print("{} {} {} @ {}".format(msg.side, msg.size, msg.tradedProductId, msg.price))


stream.on_recv(on_message)

ioloop.IOLoop.instance().start()
