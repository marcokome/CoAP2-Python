CoAP 2 -- The Python library
==================================

This library is a python 3 implementation of a proposal for a better IoT protocol over IP. It is a client and server library with the idea to enhance the `CoAP`_ paradigma by adding to synchronous an asynchronous requests, 2 more features, both very essential to IoT: Dynamic/Smart discovery and Publish/Subscribe logic. With this protocol alone, no more need therefore for mDNS and MQTT, respectively for zero-configuration and notifications when building a connected device. The details of the protocol are depicted in article `CoAP Enhancement For a Better IoT Centric Protocol: CoAP 2.0`_.

.. _`Constrained Application Protocol`: http://coap.technology/
.. _'CoAP Enhancement For a Better IoT Centric Protocol: CoAP 2.0`: https://ieeexplore.ieee.org/abstract/document/8554494

Goal
-----------

The purpose of this library is threefold:
* Performing a smart discovery over a network. A node can be retrieved with a hostname or thanks to the services it can provide. The services are also known as 'resources'. An all purpose multicast is also possible but it's not recommended as the purpose of this feature is to reduce latency and energy spent during the multicast.
* Performing publish/subscribe requests. A CoAP2 client can subscribe to a node resource with rules ``<, >, and, or, ... `` so that only notifications of interest will be received. 
* Performing synchronous ansynchrounous requests. This feature is already covered by COAP, the library is offering a more convenient way to perfom it. 

Usage/Library integrations
--------------------------

At this stage of the development, the library is able to:
* Easily describe a server thanks to python decorators
```python
from coap2 import Coap2

c = Coap2()

@c.resource('/root', observable=True)
def test():
	return "Hello root"

@c.resource('/root/child', methods=['POST'], observable=True, separate=False)
def test2():
	print("Hello root's child !")

c.run() 
```

**``methods`` refers to CRUD methods ``GET``, ``PUT``, ``POST``, ``DELETE``
**Other parameters of CoAP2.resource are:
***``observable``: which means that a client can subscribe to the resource
***``separate``: which means that the resource will be long to answer back. This is an asynchronous communication.
***``discoverable``: which means that the resource is visible for the discovery.
* Lookout for node with the hostname
```python
from coap2 import Coap2

c = Coap2()
c.discover("marcokome.local")
```
* Lookout for node with the resources
```python
from coap2 import Coap2

c = Coap2()
c.discover(['/root', '/root/child'])
```
* A callback function can be used to collect the answer
```python
from coap2 import Coap2

c = Coap2()
def on_discovery(**res):
	print("Hostname: {},\nAddress: {},\nResources: {}".format(res['hn'], res['ip'], [k for k in json.loads(res['rs']).keys()]))

c.discover("marcokome.local", , callback=on_discovery)
```

Features / Standards
--------------------

This library supports the following standards in full or partially:

* RFC7252_ (CoAP): missing are a caching and cross proxy implementation, proper
  multicast (support is incomplete); DTLS support is not supported yet,
  and lacking some security properties.
* RFC7959_ (Blockwise): Multicast exceptions missing.

If something described by one of the standards but not implemented, it is
considered a bug; please file at the `github issue tracker`_. (If it's not on
the list or in the excluded items, file a wishlist item at the same location).

.. _RFC7252: https://tools.ietf.org/html/rfc7252
.. _RFC7641: https://tools.ietf.org/html/rfc7641
.. _RFC7959: https://tools.ietf.org/html/rfc7959
.. _RFC7967: https://tools.ietf.org/html/rfc7967
.. _RFC8132: https://tools.ietf.org/html/rfc8132
.. _RFC8323: https://tools.ietf.org/html/rfc8323
.. _RFC8613: https://tools.ietf.org/html/rfc8613
.. _draft-ietf-core-resource-directory: https://tools.ietf.org/html/draft-ietf-core-resource-directory-14

Dependencies
------------

The library works on ``python 3.5.2`` or newer. Before using the library, just make a quick ``pip install -r requirements.txt``, then you are ready to try on the samples of code available in the tests_ folder.

Development
-----------

Currently under development: 
* Publish/Subscribe
* CRUD requests on synchronous and asynchronous mode.


Licensing
---------

CoAP2 is published under the MIT License, see LICENSE_ for details.

Don't hesitate to contact me for any enhancement or discussion

Copyright (c) 2020-2021 Marco KOME <marcokome@gmail.com/>,

.. _LICENSE: LICENSE

