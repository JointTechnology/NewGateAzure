# Socket server in python using select function
 
import socket, select
import urllib, urllib2, time, datetime, gc
import sys
import struct
from array import array

class bits(object):
    def __init__(self,value=0):
        self._d = value

    def __getitem__(self, index):
        return (self._d >> index) & 1 

    def __setitem__(self,index,value):
        value    = (value&1L)<<index
        mask     = (1L)<<index
        self._d  = (self._d & ~mask) | value

    def __getslice__(self, start, end):
        mask = 2L**(end - start) -1
        return (self._d >> start) & mask

    def __setslice__(self, start, end, value):
        mask = 2L**(end - start) -1
        value = (value & mask) << start
        mask = mask << start
        self._d = (self._d & ~mask) | value
        return (self._d >> start) & mask

    def __int__(self):
        return self._d

def hexdump(src, length=16):
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    lines = []
    for c in xrange(0, len(src), length):
        chars = src[c:c+length]
        hex = ' '.join(["%02x" % ord(x) for x in chars])
        printable = ''.join(["%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in chars])
        lines.append("%04x  %-*s  %s\n" % (c, length*3, hex, printable))
    return ''.join(lines)

def Read_Coil_Regs(data):
    global CoilRegs
    recvStruct = '>hhhBBhh'
    recvStructSize = struct.calcsize(recvStruct)
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    TransID , ProtoColID, PacketLength, UnitID, FC, StartAddress, RegisterCount = struct.unpack(recvFormat, data)
    ReturnSize = (RegisterCount + 7) // 8
    datatranStruct = '>hhhBBB'# + str(ReturnSize) + 'b'
    datatranStructSize = struct.calcsize(datatranStruct)
#    datatranFormat = '%s%dx' % (datatranStruct, 10 + ReturnSize - datatranStructSize)
    datatranFormat = '%s' % (datatranStruct)
    print 'datatranFormat ',datatranFormat
    print TransID, ProtoColID, PacketLength, UnitID
    print  FC, StartAddress, RegisterCount
    try:
        print CoilRegs[StartAddress:StartAddress+RegisterCount]
        sys.stdout.write(hexdump(struct.pack('L', CoilRegs[StartAddress:StartAddress+RegisterCount])[0:ReturnSize+1]))
        sys.stdout.write(hexdump(struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+ReturnSize, UnitID, FC, ReturnSize) + struct.pack('L', CoilRegs[StartAddress:StartAddress+RegisterCount])[0:ReturnSize+1]))
        return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+ReturnSize, UnitID, FC, ReturnSize) + struct.pack('L', CoilRegs[StartAddress:StartAddress+RegisterCount])[0:ReturnSize+1]
    except Exception, e: 
        print e
        return


def Read_Input_Regs(data):
    recvStruct = '>hhhBBhh'
    recvStructSize = struct.calcsize(recvStruct)
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    TransID , ProtoColID, PacketLength, UnitID, FC, StartAddress, RegisterCount = struct.unpack(recvFormat, data)
    datatranStruct = '>hhhBBB' + str(RegisterCount) + 'h'
    datatranStructSize = struct.calcsize(datatranStruct)
    datatranFormat = '%s%dx' % (datatranStruct, 10 + (2*RegisterCount) - datatranStructSize)
    print 'datatranFormat ',datatranFormat
    print TransID, ProtoColID, PacketLength, UnitID
    print  FC, StartAddress, RegisterCount
    try:
        print HoldRegs[StartAddress:StartAddress+RegisterCount]
        return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+(2*RegisterCount), UnitID, FC, 2*RegisterCount, *InputRegs[StartAddress:StartAddress+RegisterCount])
    except Exception, e: 
        print e
        return

def Read_Holding_Regs(data):
    global HoldRegs
    recvStruct = '>hhhBBhh'
    recvStructSize = struct.calcsize(recvStruct)
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    TransID , ProtoColID, PacketLength, UnitID, FC, StartAddress, RegisterCount = struct.unpack(recvFormat, data)
    datatranStruct = '>hhhBBB' + str(RegisterCount) + 'h'
    datatranStructSize = struct.calcsize(datatranStruct)
    datatranFormat = '%s%dx' % (datatranStruct, 10 + (2*RegisterCount) - datatranStructSize)
    print 'datatranFormat ',datatranFormat
    print TransID, ProtoColID, PacketLength, UnitID
    print  FC, StartAddress, RegisterCount
#    print HoldRegs
    try:
        print HoldRegs[StartAddress:StartAddress+RegisterCount]
        return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+(2*RegisterCount), UnitID, FC, 2*RegisterCount, *HoldRegs[StartAddress:StartAddress+RegisterCount])

    except Exception, e: 
        print e
        return
#    return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+(2*RegisterCount), UnitID, FC, 2*RegisterCount, *HoldRegs[StartAddress:StartAddress+RegisterCount])

def Write_Coil_Reg(data):
    global CoilRegs
    recvStruct = '>hhhBBhBB'
    recvStructSize = struct.calcsize(recvStruct)
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    TransID , ProtoColID, PacketLength, UnitID, FC, WriteAddress, RegisterValue, Filler = struct.unpack(recvFormat, data)
    datatranStruct = '>hhhBBhBB'
    datatranStructSize = struct.calcsize(datatranStruct)
    datatranFormat = '%s%dx' % (datatranStruct, 10 + 2 - datatranStructSize)
    print 'datatranFormat ',datatranFormat
    print TransID, ProtoColID, PacketLength, UnitID
    print  FC, WriteAddress, RegisterValue
    try:
        CoilRegs[WriteAddress:WriteAddress+1] = RegisterValue
        return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+2, UnitID, FC, WriteAddress, RegisterValue, Filler)
    except Exception, e: 
        print e
        return

def Write_Holding_Reg(data):
    global HoldRegs
    recvStruct = '>hhhBBhh'
    recvStructSize = struct.calcsize(recvStruct)
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    TransID , ProtoColID, PacketLength, UnitID, FC, WriteAddress, RegisterValue = struct.unpack(recvFormat, data)
    datatranStruct = '>hhhBBhh'
    datatranStructSize = struct.calcsize(datatranStruct)
    datatranFormat = '%s%dx' % (datatranStruct, 10 + 2 - datatranStructSize)
    print 'datatranFormat ',datatranFormat
    print TransID, ProtoColID, PacketLength, UnitID
    print  FC, WriteAddress, RegisterValue
    HoldRegs[WriteAddress-1] = RegisterValue
    return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+2, UnitID, FC, WriteAddress, RegisterValue)

def Write_Coil_Regs(data):
    global CoilRegs
    recvStruct = '>hhhBBhhBB'
    recvStructSize = struct.calcsize(recvStruct)
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    TransID , ProtoColID, PacketLength, UnitID, FC, WriteAddress, BitCount, ByteCount, RegisterValues = struct.unpack(recvFormat, data)
    datatranStruct = '>hhhBBhh'
    datatranStructSize = struct.calcsize(datatranStruct)
    datatranFormat = '%s%dx' % (datatranStruct, 10 + 2 - datatranStructSize)
    print 'datatranFormat ',datatranFormat
    print TransID, ProtoColID, PacketLength, UnitID
    print  FC, WriteAddress, BitCount, ByteCount, RegisterValues
    try:
        CoilRegs[WriteAddress:WriteAddress+BitCount] = RegisterValues
        return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+2, UnitID, FC, WriteAddress, BitCount)
    except Exception, e: 
        print e
        return

def Write_Holding_Regs(data):
    global HoldRegs
    recvStruct = '>hhhBBhhB'
    recvStructSize = (len(data) - struct.calcsize(recvStruct)) / 2
    recvStruct = recvStruct + str(recvStructSize) + 'h'
    recvStructSize = struct.calcsize(recvStruct)     
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    unpacked = struct.unpack(recvFormat, data)
    try:
        (TransID , ProtoColID, PacketLength, UnitID, FC, WriteAddress, WordCount, ByteCount) = unpacked[:8]
        HoldRegs[WriteAddress-1:WriteAddress+WordCount-1] = array("i",unpacked[8:])
#        (TransID , ProtoColID, PacketLength, UnitID, FC, WriteAddress, WordCount, ByteCount), HoldRegs[64:66] = unpacked[8:], unpacked[:8]
    except Exception, e: print e
    datatranStruct = '>hhhBBhh'
    print unpacked[8:]
    datatranStructSize = struct.calcsize(datatranStruct)
    datatranFormat = '%s%dx' % (datatranStruct, 10 + 2 - datatranStructSize)
    print 'datatranFormat ',datatranFormat
    print TransID, ProtoColID, PacketLength, UnitID
    print  FC, WriteAddress
    
    return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+2, UnitID, FC, WriteAddress, WordCount)

def Read_Input_Reg(data):
    recvStruct = '>hhhBBhh'
    recvStructSize = struct.calcsize(recvStruct)
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    TransID , ProtoColID, PacketLength, UnitID, FC, StartAddress, RegisterCount = struct.unpack(recvFormat, data)
    datatranStruct = '>hhhBBB' + str(RegisterCount) + 'h'
    datatranStructSize = struct.calcsize(datatranStruct)
    datatranFormat = '%s%dx' % (datatranStruct, 10 + (2*RegisterCount) - datatranStructSize)
    print 'datatranFormat ',datatranFormat
    print TransID, ProtoColID, PacketLength, UnitID
    print  FC, StartAddress, RegisterCount
    return struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+(2*RegisterCount), UnitID, FC, 2*RegisterCount, *InputRegs[StartAddress-1])

def ModbusPacket(data):
    recvStruct = '>hhhBBhh'
    recvStructSize = struct.calcsize(recvStruct)
    recvFormat = '%s%dx' % (recvStruct, len(data) - recvStructSize)
    TransID , ProtoColID, PacketLength, UnitID, FC, StartAddress, RegisterCount = struct.unpack(recvFormat, data)
    print 'Connect by', addr
    print 'nice try'
    sys.stdout.write(hexdump(data))
    try:
        if FC == 1:
            datatran = Read_Coil_Regs(data)
        elif FC == 3:
            datatran = Read_Holding_Regs(data)
        elif FC == 4:
            datatran = Read_Input_Regs(data)
        elif FC == 5:
            datatran = Write_Coil_Reg(data)
        elif FC == 6:
            datatran = Write_Holding_Reg(data)
        elif FC == 15:
            datatran = Write_Coil_Regs(data)
        elif FC == 16:
            datatran = Write_Holding_Regs(data)
    except Exception, e: print e
#    datatran = struct.pack(datatranFormat, TransID , ProtoColID, PacketLength+(2*RegisterCount), UnitID, FC, 2*RegisterCount, *datavalues)
    return (datatran)

def toJSON(json_data):
    s=""
    for key,value in json_data.items():
        if len(s) > 0:
            s = s + ", "
        if type(value) == dict:
            s = s + '"%s" : %s' % (key, toJSON(value))
        else:
            s = s + '"%s" : "%s"' % (key, value)
    return "{" + s + "}"

def toJSON(json_data):
    s=""
    for key,value in json_data.items():
        if len(s) > 0:
            s = s + ", "
        if type(value) == dict:
            s = s + '"%s" : %s' % (key, toJSON(value))
        else:
            s = s + '"%s" : "%s"' % (key, value)
    return "{" + s + "}"

def packet_toDict(data):
    f = struct.unpack('>B',(data[28:29]))
    numvals = f[0] - 2
    sensor_list = {}
    for i in range(0, numvals):
        snum = struct.unpack('>l',(data[29 + (i * 10):33 + (i * 10)]))
        f = struct.unpack('>f',(data[35 + (i * 10):39 + (i * 10)]))
        sensor_list.update({str(snum[0]) : str(f[0])})
#    body_data = { "deviceId": "Redlion", "time": str(datetime.datetime.now())}
    body_data = { "deviceId": "Redlion", "iodb": sensor_list, "time": str(datetime.datetime.now())}
#    body_data = { "deviceId": "Redlion", "iodb": {str(snum[0]) : str(f[0])}, "time": str(datetime.datetime.now())}
    return body_data
    
    
def send_iot(data):
    global iot_device_id
    global iot_hub_name
    global iot_saskey

 #   iot_device_id = 'HTTP_Device'
 #   iot_hub_name = 'https://winiothub.azure-devices.net/devices/'
    iot_endpoint = iot_hub_name + iot_device_id + '/messages/events?api-version=2016-02-03'
 #   iot_saskey = 'SharedAccessSignature sr=winiothub.azure-devices.net%2Fdevices%2FHTTP_Device&sig=o7dndsA%2FJOnkzYRUhqAwMrQXVhOTpIJqJqILyGDdQAc%3D&se=1522414643'
#    sas_header = {'Authorization': 'SharedAccessSignature sr=winiothub.azure-devices.net%2Fdevices%2FHTTP_Device&sig=o7dndsA%2FJOnkzYRUhqAwMrQXVhOTpIJqJqILyGDdQAc%3D&se=1522414643'}
    sas_header = {'Authorization': iot_saskey}
    try:
 #       f = struct.unpack('>f',(data[35:39]))
 #       body_data = { "gateway_serial": "123", "readingvalue":str(f), "date": str(datetime.datetime.now())}
        body_data = toJSON(packet_toDict(data))
        print body_data
        iot_request = urllib2.Request(iot_endpoint, str(body_data), sas_header)
        try:
            resp = urllib2.urlopen(iot_request)
        except urllib2.HTTPError, e:
            raise
            if e.code ==  204:
                print '204'
            else:
                print 'Error = ' + e.code
        contents = resp.read()
        print gc.collect()
        resp.close()
    except urllib2.HTTPError, e:
        if e.code == 204:
            print '204'
            pass
        else:
            print 'error' 

def DatabaseInit():
    return



CONNECTION_LIST = []    # list of socket clients
RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
PORT = 5000
MODBUSPORT = 502
NREGS = 200

#fo = open('WEB/python/AzureConfig.txt','r')
#iot_device_id = fo.readline()
#iot_hub_name = fo.readline()
#iot_saskey = fo.readline()
#print iot_device_id
#print iot_hub_name
#print iot_saskey

iot_device_id = 'HTTP_Device'
iot_hub_name = 'https://winiothub.azure-devices.net/devices/'
iot_saskey = 'SharedAccessSignature sr=winiothub.azure-devices.net%2Fdevices%2FHTTP_Device&sig=o7dndsA%2FJOnkzYRUhqAwMrQXVhOTpIJqJqILyGDdQAc%3D&se=1522414643'

CoilRegs = bits()
CoilRegs[0:NREGS] = 0
CoilRegs[3:6] = 7
CoilRegs[15:18] = 7
CoilRegs[30:33] = 7
HoldRegs = array("i", [0]) * NREGS
HoldRegs[65]=5
InputRegs = array("i", [0]) * NREGS
InputRegs[1]=55

         
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# this has no effect, why ?
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_address = ('', PORT)
server_socket.bind(server_address)
server_socket.listen(10)
 
server_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# this has no effect, why ?
#server_socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_address1 = ('',MODBUSPORT)
server_socket1.bind(server_address1)
server_socket1.listen(10)

# Add server socket to the list of readable connections
CONNECTION_LIST.append(server_socket)
CONNECTION_LIST.append(server_socket1)

datavalues = array("i",[22, 41, 69, 33, 66, 199, 299])
datavalues1 = array("i",[22, 44, 62, 133, 6, 9, 189])

print "Chat server started on port " + str(PORT)
 
while 1:
    # Get the list sockets which are ready to be read through select
    read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
 
    for sock in read_sockets:
             
        #New connection
        if sock == server_socket1:
            sockfd, addr = server_socket1.accept()
            CONNECTION_LIST.append(sockfd)
            print "Client (%s, %s) connected" % addr
            print "Modbus socket"

        elif sock == server_socket:
            # Handle the case in which there is a new connection recieved through server_socket
            sockfd, addr = server_socket.accept()
            CONNECTION_LIST.append(sockfd)
            print "Client (%s, %s) connected" % addr
                 
        #Some incoming message from a client
        else:
            # Data recieved from client, process it
            try:
                #In Windows, sometimes when a TCP program closes abruptly,
                # a "Connection reset by peer" exception will be thrown
                a = sock.getsockname()
                # echo back the client message
                print 'a[1] = '
                if a[1] == PORT:
                    data = sock.recv(RECV_BUFFER)
                    if len(data) > 0:
                        print 'Telnet = ' 
                        sys.stdout.write(hexdump(data))
                        sys.stdout.write(hexdump(data[35:39]))
                        f = struct.unpack('>f',(data[35:39]))
                        print f
                        c = f[0]
                        send_iot(data)
                        #print type(c)
                        #HoldRegs[1] = int(c)
                        #print HoldRegs[1]
                        #sys.stdout.write(hexdump(data[45:49]))
                        #f = struct.unpack('f',(data[45:49]))
                        #print f
                        #c = f[0]
                        #print type(c)
                        #HoldRegs[2] = int(c)
                        #print HoldRegs[2]
                    else:
                        print 'Closing Telnet'
                        sock.close()
                        CONNECTION_LIST.remove(sock)
                elif data:
                    data = sock.recv(RECV_BUFFER)
                    data = ModbusPacket(data)
                    sock.send(data)
                 
#            # client disconnected, so remove from socket list
            except Exception, e:
#                broadcast_data(sock, "Client (%s, %s) is offline" % addr)
                print e
                print "Client (%s, %s) is offline" % addr
                sock.close()
                CONNECTION_LIST.remove(sock)
                continue
         
server_socket.close()
server_socket1.close()