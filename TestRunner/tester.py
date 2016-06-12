import sys
from datetime import datetime
from time import sleep
from rediscluster import StrictRedisCluster
import logging

startup_nodes = [
    {"host": "192.168.56.21", "port": "6379"},
    {"host": "192.168.56.22", "port": "6379"},
    {"host": "192.168.56.23", "port": "6379"}]
r = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
print(r.set('foo', 'bar'))
print(r.get('foo'))

p = r.pubsub()
def my_handler(message):
    global LastReceivedMessage
    #print "Received (%s,%s)" % (message['channel'], message['data'])
    if 'data' in message.keys():
        shard = int(message['channel'])
        actualMessage = int(message['data'])
        print "%s%sReceived %s" % (' '*26, '\t'*shard, actualMessage)
        if LastReceivedMessage+1 != actualMessage:
            print "Missed %s messages" %(actualMessage-LastReceivedMessage-1)
        LastReceivedMessage = actualMessage

#p.psubscribe(**{'my-*': my_handler}) # throws an error
p.subscribe(**{'0': my_handler})
p.subscribe(**{'1': my_handler})
p.subscribe(**{'2': my_handler})
p.subscribe(**{'3': my_handler})
p.subscribe(**{'4': my_handler})
p.subscribe(**{'5': my_handler})
p.get_message() # to see that there was a subscription
LastReceivedMessage = -1
r.publish('0', LastReceivedMessage+1)
p.get_message()

thread = p.run_in_thread(sleep_time=0.001)

COUNT = 1000
SLEEP = 0.1
message_id = 1
print 'LastReceivedMessage=',LastReceivedMessage
sleep(SLEEP)
print 'LastReceivedMessage=',LastReceivedMessage
try:
    while message_id <= COUNT:
        shard = message_id % 6
        key = 'key' + str(shard)
        payload = str(message_id)
        print "%s%spublishing %s" % (str(datetime.now()),'\t'*shard, message_id)
        count = r.publish(str(shard), payload)
        try:
            ans = r.set(key, str(message_id))
        except:
            print("Set Error:", sys.exc_info()[0])
            pass
        sleep(SLEEP)
        try:
            actualPayload = r.get(key)
        except:
            print("Get Error:", sys.exc_info()[0])
            pass
        if actualPayload != payload:
            print "Missed %s payloads for %s" %(message_id-int(actualPayload), shard)
        message_id += 1
except KeyboardInterrupt:
    pass

thread.stop()
p.close()
print "done"
