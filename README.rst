

CoAP 2 -- The Python library
==================================

This library is a python 3 implementation of a proposal for a better IoT protocol over IP. It is a client and server library with the idea to enhance the `CoAP`_ paradigma by adding to synchronous an asynchronous requests, 2 more features, both very essential to IoT: Dynamic/Smart discovery and Publish/Subscribe logic. With this protocol alone, no more need therefore for mDNS and MQTT, respectively for zero-configuration and notifications when building a connected device. The details of the protocol are depicted in article `CoAP Enhancement For a Better IoT Centric Protocol: CoAP 2.0`_.

.. _`CoAP`: http://coap.technology/
.. _`CoAP Enhancement For a Better IoT Centric Protocol: CoAP 2.0`: https://ieeexplore.ieee.org/abstract/document/8554494

Goal
-----------

The purpose of this library is threefold:

* Performing a smart discovery over a network. A node can be retrieved with a hostname or thanks to the services it can provide. The services are also known as 'resources'. An all purpose multicast is also possible but it's not recommended as the purpose of this feature is to reduce latency and energy spent during the multicast.
* Performing publish/subscribe requests. A CoAP2 client can subscribe to a node resource with rules ``<, >, and, or, ...`` so that only notifications of interest will be received. 
* Performing synchronous ansynchrounous requests. This feature is already covered by COAP, the library is offering a more convenient way to perfom it. 

Dependencies
------------

The library works on ``python 3.5.2`` or newer. Before using the library, make sure you have ``git`` and ``pip3`` installed first. Then in the appropriate folder make

.. code-block:: text
	
	git clone https://github.com/marcokome/CoAP2-Python.git. 
	cd CoAP2-Python/tests
	
You are now ready to try the samples available in the tests_ folder.

.. _tests: tests


Usage/Library integrations
--------------------------

At this stage of the development, the library is able to:

1. Easily describe a server thanks to python decorators

   .. code-block:: python

	from coap2 import Coap2

	c = Coap2()

	@c.resource('/root', observable=True)
	def test():
		return "Hello root"

	@c.resource('/root/child', methods=['POST'], observable=True, separate=False)
	def test2():
		print("Hello root's child !")

	c.run()	

   The output should look like the following:

   .. code-block:: text

	CoAp2 server is running on marcokome.local:5683
	Listening on 192.168.1.73...
	Available resources (DEBUG):
	{'/root': {'options': {'discoverable': True,
				 'methods': ['GET'],
				 'observable': True,
				 'separate': False},
		     'rule': <function test3 at 0x7fe48322bd08>},
	 '/root/child': {'options': {'discoverable': True,
			       'methods': ['GET'],
			       'observable': True,
			       'separate': False},
		   'rule': <function test at 0x7fe485493620>},


   CoAP2.resource are:

   * ``methods``: which is a table with one or many of the following CRUD methods ``GET``, ``PUT``, ``POST``, ``DELETE``.
   * ``observable``: which means that a client can subscribe to the resource
   * ``separate``: which means that the resource will be long to answer back. This is an asynchronous communication.
   * ``discoverable``: which means that the resource is visible for the discovery.

2. Lookout for node with the hostname:

   .. code-block:: python
   
	from coap2 import Coap2

	c = Coap2()
	c.discover("marcokome.local")
	
   The output should contain the following:
   
   .. code-block:: text
   
	**Default discovery callback:
	---------------------------------
	ip:('192.168.1.73', 5683),
	hn:marcokome.local,
	rs:{"/root": {"options": {"discoverable": true, "observable": true, "separate": false, "methods": ["GET"]}}, "/root/child": {"options": {"discoverable": true, "observable": true, "separate": false, "methods": ["POST"]}}, "/random": {"options": {"discoverable": true, "observable": true, "separate": false, "methods": ["GET"]}}}

   With the hostname filtering, only one response is expected. The above result is given via a default callback.

3. Lookout for node with the resources

   .. code-block:: python
   
	from coap2 import Coap2

	c = Coap2()
	c.discover(['/root', '/root/child'])

   With this method, many responses are expected.

4. A callback function can be used to collect the answer

   .. code-block:: python
	
	from coap2 import Coap2
	import json

	c = Coap2()
	def on_discovery(**res):
		print("Hostname: {},\nAddress: {},\nResources: {}".format(res['hn'], res['ip'], [k for k in json.loads(res['rs']).keys()]))

	c.discover("marcokome.local", , callback=on_discovery)
	
   In a custom callback, the result is processed. The example of callback in the above code, should print the following text:

   .. code-block:: text
	
	Hostname: marcokome.local,
	Address: ('192.168.1.73', 5683),
	Resources: ['/root', '/root/child', '/random']


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
.. _RFC7959: https://tools.ietf.org/html/rfc7959
.. _`github issue tracker`: issues

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

