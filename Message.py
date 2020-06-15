#CoAp2 message based on RFC... and the article...
import parameters
import json
from itertools import chain

class Message():
    def __init__(self, **argv):

        if 'raw_data' in argv:
            #print(argv['raw_data'])
            self._decode(argv['raw_data'])
        else:
            self.version = argv['version'] if 'version' in argv else parameters.VERSION
            self.type    = argv['type']    if 'type'    in argv else 0
            self.code    = argv['code']    if 'code'    in argv else 0
            self.mid     = argv['mid']     if 'mid'     in argv else 0
            self.token   = argv['token']   if 'token'   in argv else b''
            self.options = argv['options'] if 'options' in argv else b''
            self.payload = argv['payload'] if 'payload' in argv else b''

            self._encode()


    def _encode(self):
        self.message = []

        #TKL = len(self.token) if self.token is not None else
        self.message += [self.version<<6 | self.type<<4 | len(self.token)]
        self.message += [self.code]
        #self.message += self._int2buf(self.mid,2)
        self.message += (self.mid).to_bytes(2, 'big')
        self.message += self._int2buf(self.token,len(self.token))
        #self.message += (self.token).to_bytes(len(self.token), 'big')
        self.message += self._encodeOptions(self.options)
        self.message += self._encodePayload(self.payload)

    def _decode(self, raw_data):

        self.version = (raw_data[0]>>6)&0x03
        self.type = (raw_data[0]>>4)&0x03 # Version 1 shift register
        TKL = raw_data[0]&0x0f
        self.code = raw_data[1]
        self.mid = int.from_bytes(raw_data[2:4], 'big')
        self.token = int.from_bytes(raw_data[5:5+TKL], 'big') if TKL == 0 else b''

        header_payload = raw_data[4:] if TKL == 0 else raw_data[5+TKL+1:]

        # If Empty message (options,payload) is empty
        self.options, self.payload = self._decodeOptionsAndPayload(header_payload) if header_payload else (None, b'')


    def _buf2int(self, buf):
        val  = 0
        for i in range(len(buf)):
            val += buf[i]<<(8*(len(buf)-1-i))
        return val

    def _int2buf(self, val,length):
        returnVal  = []
        for i in range(length,0,-1):
            returnVal += [val>>(8*(i-1))&0xff]

        return returnVal

    def _encode_extended_field(self, value):
        if value >= 0 and value < 13:
            return (value, (0).to_bytes(1, 'big'))
        elif value >= 13 and value < 269:
            return (13, (value - 13).to_bytes(1, 'big'))
            #return (13, (value - 13))
        elif value >= 269 and value < 65804:
            return (14, (value - 269).to_bytes(2, 'big'))
            #return (14, (value - 269))
        else:
            raise ValueError("Value out of range.")

    def _decode_extended_field(self, value, raw_data):
        #return (the code, nbr of bytes to jump)
        if value >= 0 and value < 13:
            return (value, 1)
        elif value == 13:
            return (int(raw_data[0]) + 13, 1)
        elif value == 14:
            return (int.from_bytes(raw_data[1:2], 'big') + 269, 2)
        else:
            raise UnparsableMessage("Option contained partial payload marker.")

    def _encodeOptions(self, options):
        encoded = []

        if not options:
            return encoded

        for op_key, op_val in options.items():
            if op_key not in parameters.OPTIONS.keys():
                raise Exception("Option '{}' not supported yet...".format(op_key))
            else:
                # Encode URI path accordind to rfc7252#...
                if op_key == 'Uri-Path':
                    encoded += self._encodeURI(op_val)
                    '''
                elif op_key == 'Uri-Query':
                    encoded += self._encodeQuery(op_val)
                    '''
                else:
                    delta, extended_delta = self._encode_extended_field(parameters.OPTIONS[op_key])

                    if op_key == 'Content-Format':
                        if op_val in parameters.CONTENT_FORMAT.keys():
                            op_val = parameters.CONTENT_FORMAT[op_val]
                        else:
                            raise Exception('Content Format {} not supported yet...'.format(op_val))

                    length, extended_length = self._encode_extended_field(len(op_val) if type(op_val) is not int else 1)

                    encoded += [delta << 4 | length]
                    encoded += [e for e in extended_delta]
                    encoded += [e for e in extended_length]
                    encoded += [ord(b) for b in op_val] if type(op_val) is not int else op_val.to_bytes(1, 'big')
                    '''
                    print('[{}|{}]'.format(delta, length))
                    print('[ {} ]'.format(extended_delta))
                    print('[ {} ]'.format(extended_length))
                    print('[{}]'.format([ord(b) for b in op_val])) if type(op_val) is not int else op_val.to_bytes(1, 'big')
                    '''
        return encoded

    def _encodeURI(self, uri):
        encoded = []

        ops = uri.split('/') if '/' in uri else uri
        ops.remove('') if '' in ops else None

        for i,o in enumerate(ops):
            #print(o)
            if i == 0:
                delta, extended_delta = self._encode_extended_field(parameters.OPTIONS['Uri-Path'])
            else:
                delta, extended_delta = self._encode_extended_field(parameters.OPTIONS['/'])

            length, extended_length = self._encode_extended_field(len(o))

            encoded += [delta << 4 | length]
            encoded += [e for e in extended_delta]
            encoded += [e for e in extended_length]
            encoded += [ord(b) for b in o] if type(o) is not int else o.to_bytes(1, 'big')
            #print(encoded)

        return encoded

    def _encodePayload(self, payload):
        encoded = []
        if payload:
            encoded += [parameters.PAYLOAD_MARKER]
            if 'Content-Format' in self.options:
                if self.options['Content-Format'] == 'text/plain':
                    encoded += [ord(b) for b in payload]
                elif self.options['Content-Format'] == 'json':
                    encoded += [ord(b) for b in json.dumps(payload)]


        #print("Encoded payload: ")
        #print(encoded)
        return encoded

    def _encodeQuery(self, query):
        encoded = []
        delta, extended_delta = self._encode_extended_field(parameters.OPTIONS['Uri-Query'])

        '''
        for k,v in query.items():
            q = '{}={}'.format(k,v)
            length, extended_length = self._encode_extended_field(len(q))
            encoded += [delta << 4 | length]
            encoded += [e for e in extended_delta]
            encoded += [e for e in extended_length]
            #encoded += [ord(b) for b in o] if type(q) is not int else q.to_bytes(1, 'big')
            encoded += [ord(b) for b in q]
        '''
        length, extended_length = self._encode_extended_field(len(query))
        encoded += [delta << 4 | length]
        encoded += [e for e in extended_delta]
        encoded += [e for e in extended_length]
        #encoded += [ord(b) for b in o] if type(q) is not int else q.to_bytes(1, 'big')
        encoded += [ord(b) for b in query]

        return encoded

    def _decodeOptionsAndPayload(self, rawbytes):

        options = []
        payload = b''
        optionNumber = 0

        while True:
            option, optionNumber = self._parseOption(rawbytes, optionNumber)

            if not option:
                break
            elif '/' in option:
                for o in options:
                    if 'Uri-Path' in o:
                        o['Uri-Path'] += '/'+option['/']
                        break
            elif 'Content-Format' in option:
                for k,f in enumerate(parameters.CONTENT_FORMAT):
                    if k == option['Content-Format']:
                        option['Content-Format'] = f
                        options.append(option)
                        break
                        '''
            elif 'Uri-Query' in option:

                o = option['Uri-Query'].split('=')
                q = dict({o[0]:o[1]})

                if next((True for i in options if 'Uri-Query' in i), False):
                    prev_uri_query = next((i for i in options if 'Uri-Query' in i), None)
                    q = {k:v for k,v in chain(prev_uri_query['Uri-Query'].items(),q.items())}
                    #print('previous q {}'.format(prev_uri_query))
                    #print('new q {}'.format(q))
                    options.remove(prev_uri_query)

                options.append({'Uri-Query':q})
                #print(options)

                options.append(option)
                '''
            else:
                options.append(option)

            if optionNumber >= len(rawbytes)-2:
                break
            elif rawbytes[optionNumber] is parameters.PAYLOAD_MARKER:
                payload = rawbytes[optionNumber+1:]
                break

        return (options, payload)

    def _parseOption(self, message, optionIndex):
        #     *-----------*-----------*
        #     | OptDelta  | OptLength |
        #    *-----------*-----------*
        #    |    OptDelta Ext       |
        #   *-----------------------*
        #   |    OptLenght Ext      |
        #  *-----------------------*
        #  |      OptValue        |
        # *-----------------------*
        # For devlpt...
        # Follow https://github.com/openwsn-berkeley/coap/blob/develop/coap/coapOption.py

        # Read the first byte...
        delta = (message[optionIndex]>>4)&0x0f
        length = message[optionIndex] & 0x0f
        # Read all the information in the extensions
        delta, len_delta_ext = self._decode_extended_field(delta, message[optionIndex+1:])
        length, len_length_ext = self._decode_extended_field(length, message[optionIndex+1+len_delta_ext:])
        # Read the value of the option
        nextOptionIndex = optionIndex + 1 + len_delta_ext + len_length_ext + length
        value = message[optionIndex + 1 + len_delta_ext + len_length_ext : nextOptionIndex]

        #print('delta: {}, length: {}, value: {}'.format(delta, length, value))

        for k, v in parameters.OPTIONS.items():
            if v == delta:
                if k == 'Content-Format' or k == 'Notification':
                    return ({k: int.from_bytes(value, 'big')}, nextOptionIndex)
                else:
                    return ({k: bytes(value).decode()}, nextOptionIndex)
                break

        raise Exception('Unsupported option ...')




    def send(self, socket, client=None, discovery=False):
        msg_length = len(self.message).to_bytes(2, 'big')
        #msg_chksum = _udpCheckSum(self.ip, self.client, self.port, message)
        msg_chksum = [0x00, 0x00]

        udp_body = []
        #udp_body += msg_length
        #udp_body += msg_chksum
        udp_body += self.message
        if discovery:
            #print("Sending Message in discovery: {}".format(bytearray(udp_body)))
            socket.sendto(bytearray(udp_body), (parameters.MULTICAST_V4, parameters.DEFAULT_PORT))
        else:
            #print("Sending Message: {}".format(bytearray(udp_body)))
            socket.sendto(bytearray(udp_body), client)

    #TODO
    def _udpCheckSum(self, srcIp,destIp,srcPort,destPort,payload):

        pseudoPacket  = []
        '''
        # IPv6 pseudo-header
        pseudoPacket += srcIp                         # Source address
        pseudoPacket += destIp                        # Destination address
        pseudoPacket += int2buf(8+len(payload),4)     # UDP length
        pseudoPacket += [0x00]*3                      # Zeros
        pseudoPacket += [17]                          # next header
        '''
        # UDP pseudo-header
        pseudoPacket += self._int2buf(srcPort, 2)           # Source Port
        pseudoPacket += self._int2buf(destPort, 2)          # Destination Port
        pseudoPacket += self._int2buf(len(payload), 2)      # Length
        pseudoPacket += [0x00,0x00]                   # Checksum

        pseudoPacket += payload
        if len(pseudoPacket)%2==1:
            pseudoPacket += [0x00]

        return self._checksum(pseudoPacket)

    #TODO
    def _checksum(self, byteList):
        s = 0
        for i in range(0, len(byteList), 2):
            w = byteList[i] + (byteList[i+1] << 8)
            s = self._carry_around_add(s, w)
        return ~s & 0xffff

    #TODO
    def _carry_around_add(self, a, b):
        c = a + b
        return (c & 0xffff) + (c >> 16)


    def __repr__(self):
        data = {'v':self.version,
                't':self.type,
                #'tkl': len(self.token),
                'tkl': 0,
                'code':self.code,
                'mid':self.mid,
                'token':self.token,
                'option':self.options,
                'payload':self.payload.decode() if self.payload else "---"}
        res = "CoAP2.Message:\n[{v}|{t}|{tkl}]\n[ {code} ]\n[{mid}]\n[{token}]\n{option}\n\n{payload}".format(**data)
        return res

    def __len__(self):
        return len(self.message)
