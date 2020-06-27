

# CoAP 2 -- The Python library

This library is a python 3 implementation of a proposal for a better IoT protocol over IP. It is a client and server library with the idea to enhance the [CoAP](http://coap.technology/) paradigm by adding to synchronous an asynchronous requests, 2 more features, both very essential to IoT: Dynamic/Smart discovery and Publish/Subscribe logic. With this protocol alone, no more need therefore for mDNS and MQTT, respectively for zero-configuration and notifications when building a connected device. The details of the protocol are depicted in the article [CoAP Enhancement For a Better IoT Centric Protocol: CoAP 2.0](https://ieeexplore.ieee.org/abstract/document/8554494).


Goal
-----------

From an IoT point of view, a network consists of nodes communicating with each other. A node is considered as a server and a client at the same time. In fact, it can expose a set of resources related its capabilities and request for other services over the internet.

The purpose of this library is threefold:

1. Performing a smart discovery over a network. A node can be retrieved thanks to its hostname or its resources. An all purpose multicast is also possible but not recommended as the asset of this feature is to reduce latency and energy spent during the multicast.
2. Performing publish/subscribe requests. A node can subscribe to another one with logic rules like ``<, >, or, and, ...`` so that only notifications of interest will be received.
3. Performing synchronous and asynchronous requests. This feature is already covered by COAP (respectively piggybacked and separate response), the library is offering a more convenient way to perform it.

Install / Dependencies
----------------------

The library works on ``python 3.5.2`` or newer. Before using the library, make sure you have ``git`` and ``pip3`` installed first. Then in the appropriate folder, type the following commands:

```
git clone https://github.com/marcokome/CoAP2-Python.git.
cd CoAP2-Python/tests
```

You are now ready to try the samples available in the [tests](tests) folder.


Usage
--------------------------

At this stage of the development, the library is able to:

#### Easily describe a server thanks to python decorators

```python

from coap2 import Coap2

c = Coap2()

@c.resource('/root', observable=True)
def test():
	return "Hello root"

@c.resource('/root/child', methods=['POST'], observable=True, separate=False)
def test2():
	return "Hello root's child !"

c.run()
```
 CoAP2.resource arguments are:

* ``uri``: String representing the resource address.
* ``methods``: Table with one or many of the following CRUD methods ``GET``, ``PUT``, ``POST``, ``DELETE``. Default method is ``['GET']``.
* ``observable``: Boolean meaning that a client can subscribe to the resource or not. Default is ``False``
* ``separate``: Boolean meaning that the resource will be long to answer back. Default is ``False``. If set to ``True``, then this is an asynchronous communication.
* ``discoverable``: Boolean meaning that the resource is visible for the discovery or not. Default is ``True``

#### Lookout for node with the hostname:

```python

from coap2 import Coap2

c = Coap2()
c.discover("node1.local")
```

With the hostname filtering, only one response is expected. The above result is given via a default callback.

#### Lookout for node with the resources

```python

from coap2 import Coap2

c = Coap2()
c.discover(['/root', '/root/child'])
```

With this method, many responses are expected.

#### A callback function can be used to collect the answer

```python

from coap2 import Coap2
import json

c = Coap2()
def on_discovery(**res):
	print("Hostname: {},\nAddress: {},\nResources: {}".format(res['hn'], res['ip'], [k for k in json.loads(res['rs']).keys()]))

c.discover("node1.local", callback=on_discovery)
```

In a custom callback, the result is processed. The example of callback in the above code, should print the following text:

```
Hostname: node1.local,
Address: ('192.168.1.73', 5683),
Resources: ['/root', '/root/child']
```

#### Perform synchronous CRUD requests

```python

from coap2 import Coap2

c = Coap2()

data = {"temp":12.9, "hum":2.5, "lum": 100}

req = c.post('coap://node1.local/root/child', data=data)
print("response code: {}\nresponse type: {}\nresponse: {}".format(req[0], req[1], req[2]))
```

#### Perform asynchronous CRUD requests
```python

from coap2 import Coap2

c = Coap2()

# define a callback function
def callback(**res):
  print(">Async response: code {}, type {}, payload {}".format(res['code'], res['type'], res['payload']))

req = c.get('coap://node1.local/root/child', callback=callback)

# Do other task in the main thread while waiting for the response...
print(1+1)
```

Features / Standards
--------------------

This library supports the following standards in full or partially:

* [RFC7252](https://tools.ietf.org/html/rfc7252) (CoAP): missing are a caching and cross proxy implementation, proper
  multicast (support is incomplete); DTLS support is not supported yet,
  and lacking some security properties.
* [RFC7959](https://tools.ietf.org/html/rfc7959) (Blockwise): Multicast exceptions missing.

If something described by one of the standards but not implemented, it is
considered a bug; please file at the [github issue tracker](issues).

Development
-----------

Currently under development:

* Publish/Subscribe
* Security: Integrating [OSCOR](https://tools.ietf.org/html/rfc8613) (Object Security for Constrained RESTful Environments)


Licensing
---------

CoAP2 is published under the MIT License, see [LICENSE](LICENSE) for details.

Don't hesitate to contact me for any enhancement or discussion

Copyright (c) 2020-2021 Marco KOME <marcokome@gmail.com/>,

Troubleshooting
---------------
For some reason you may have troubles when performing requests on new nodes. This malfunction is caused by your router configuration. In order to use the library without configuring the router, we recommend to cache the ip of interest first. A convenient way of doing it is to run the following code prior to any requests on a new node.

```python

from coap2 import Coap2
import utils

c = Coap2()

# Cache every node responding to the discovery request. Any type of discovery works fine.
def callback(**res):
  print("New node : {} - {}".format(res['hn'], res['ip'][0]))
  utils.cacheDNS(res['hn'], res['ip'][0])

req = c.discover(['/root'], callback=callback)

```
