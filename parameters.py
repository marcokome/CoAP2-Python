
""" CoAP Parameters """

LOCALHOST = '127.0.0.1'
MULTICAST_V4 = '224.0.1.187'
MULTICAST_V6 = 'FF0X::FD'
DEFAULT_PORT = 5683
DEFAULT_TIMOUT = 10
DEFAULT_ATTEMPT_NUMBER = 3
DEFAULT_DISCOVERY_POOLING = 5
BUFFERSIZE = 4096

VERSION = 2

QOS_0 = 0
QOS_1 = 1

COAP_HEADER = "coap://"
COAP_HEADER_SECURE = "coaps://"

TYPES = {
    'CON': 0,
    'NON': 1,
    'ACK': 2,
    'RST': 3,
    'None': None
}
# According to https://tools.ietf.org/html/rfc7252#section-12.1.1
METHODS = {
    'GET'   :1,
    'POST'  :2,
    'PUT'   :3,
    'DELETE':4,
    'EMPTY' :0
}

# According to https://tools.ietf.org/html/rfc7252#section-12.1.2
RESPONSE_CODES = {
    'Created':                      65, #2.01
    'Deleted':                      66, #2.02,
    'Valid':                        67, #2.03,
    'Bad Option':                   130, #4.02,
    'Changed':                      68, #2.04,
    'Bad Request':                  128, #4.00,
    'Unauthorized':                 129, #4.01,
    'Content':                      69, #2.05,
    'Forbidden':                    131, #4.03,
    'Not Found':                    132, #4.04,
    'Method Not Allowed':           133, #4.05,
    'Not Acceptable':               134, #4.06,
    'Precondition Failed':          140, #4.12,
    'Request Entity Too Large':     141, #4.13,
    'Unsupported Content-Format':   143, #4.15,
    'Internal Server Error':        160, #5.00,
    'Not Implemented':              161, #5.01,
    'Bad Gateway':                  162, #5.02,
    'Service Unavailable':          163, #5.03,
    'Gateway Timeout':              164, #5.04,
    'Proxying Not Supported':       165, #5.05
}

OPTIONS = {
    'If-Match'       :      1 ,
    'Uri-Host'       :      3,
    'ETag'           :      4,
    'If-None-Match'  :      5,
    'Uri-Port'       :      7,
    'Location-Path'  :      8,
    'Uri-Path'       :      11,
    '/'              :      0,
    'Content-Format' :      12,
    'Max-Age'        :      14,
    'Uri-Query'      :      15,
    'Accept'         :      17,
    'Location-Query' :      20,
    'Proxy-Uri'      :      35,
    'Proxy-Scheme'   :      39,
    'Size1'          :      60,
    'Discovery'      :      300,
    'Notification'   :      400,
    'Rule'           :      410
}

PAYLOAD_MARKER = 0xff

CONTENT_FORMAT = {
    'text/plain'   : 0 ,
    'link-format'  : 40,
    'xml'          : 41,
    'octet-stream' : 42,
    'exi'          : 47,
    'json'         : 50,
    'cbor'         : 60
}

RESOURCE_OPTIONS = ['methods', 'discoverable', 'observable', 'separate']

'''
+-------------------+---------------+
| name              | default value |
+-------------------+---------------+
| ACK_TIMEOUT       | 2 seconds     |
| ACK_RANDOM_FACTOR | 1.5           |
| MAX_RETRANSMIT    | 4             |
| NSTART            | 1             |
| DEFAULT_LEISURE   | 5 seconds     |
| PROBING_RATE      | 1 byte/second |
+-------------------+---------------+
'''
