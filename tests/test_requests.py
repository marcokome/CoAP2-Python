# -----------------------------------------------------
# Make sure the file test_server.py is running first !
# In another console type the following command
# python3 test_server.py
# -----------------------------------------------------
import sys
sys.path.append('../')

from coap2 import Coap2

c = Coap2()

data = {"temp":12.9, "hum":2.5, "lum": 100}
data2 = {"soil":"N,P,K"}

# Successful requests for the server in test_server.py
req = c.get('coap://node1.local/random')
print("response code: {}\nresponse type: {}\nresponse: {}".format(req[0], req[1], req[2]))

# Get method with parameters
req = c.get('coap://node1.local/root', data=data2)
print("response code: {}\nresponse type: {}\nresponse: {}".format(req[0], req[1], req[2]))
print("N: {}".format(json.loads(req[2]['N'])))
print("P: {}".format(json.loads(req[2]['P'])))
print("K: {}".format(json.loads(req[2]['K'])))

req = c.post('coap://node1.local/root/child', data=data)
print("response code: {}\nresponse type: {}\nresponse: {}".format(req[0], req[1], req[2]))

# Unsuccessful request because, the resource /random doesnt accept POST method.
# For response code, please refer to https://tools.ietf.org/html/rfc7252#section-12.1.2
req = c.post('coap://node1.local/random', data=data)
print("response code: {}\nresponse type: {}\nresponse: {}".format(req[0], req[1], req[2]))

# asynchronous request
# define a callback function
def callback(**res):
  print(">Async response: code {}, type {}, payload {}".format(res['code'], res['type'], res['payload']))

req = c.get('coap://node1.local/root/child/private', callback=callback)
print("Doing another task while waiting for the callback to pop up...")
