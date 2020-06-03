import socket, os, sys, struct
from Message import Message
import parameters

t = parameters.TYPES['NON']
code = parameters.METHODS['GET']
mid = 12345

options = dict()
#options['Discovery'] = '/root,/root/child'
options['Discovery'] = "raspberrypi.local"
options['Uri-Host'] = "raspberrypi.local" # the device we are looking for
options['Uri-Path'] = "/temperature/celsius"
options['Content-Format'] = parameters.CONTENT_FORMAT['text/plain']

payload = ''#'/root,/root/child' # Resources or functionalities we are looking for

#message = Message(type=t, code=code, mid=mid, options=options)
message = Message(type=t, code=code, mid=mid, options=options, payload=payload)
#print(message.message)

decode_message = Message(raw_data=message.message)
print(decode_message)

'''
print("Discovering...\n\n")
multicast_group = ('224.0.1.187', 5683)

# Create a UDP socket at client side
s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
s.settimeout(3)
ttl = struct.pack('b', 2)
s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

# Send to server using created UDP socket
#s.sendto(bytearray(udp_body), serverAddressPort)
s.sendto(bytearray(udp_body), multicast_group)

try:
    msgFromServer = s.recvfrom(bufferSize)
except socket.timeout:
    print('timed out, no more responses')
else:
    msg = "Message from {}\n".format(msgFromServer[1][0])
    print(msg)

response = Message(raw_data=msgFromServer[0])
print(response)
'''
