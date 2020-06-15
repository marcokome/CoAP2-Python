import sys
sys.path.append('../')

from coap2 import Coap2
import json

c = Coap2()

def on_discovery(**res):
	print("Hostname: {},\nAddress: {},\nResources: {}".format(res['hn'], res['ip'], [k for k in json.loads(res['rs']).keys()]))


#c.discover()
#c.discover("node1.local")
#c.discover("node1.local", callback=on_discovery)
c.discover(['/root'], callback=on_discovery)
