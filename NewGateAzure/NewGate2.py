import socket
import select
import sys
import struct
import zigbee # used to get address of radio module in the gateway

def hexdump(src, length=16):
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    lines = []
    for c in xrange(0, len(src), length):
        chars = src[c:c+length]
        hex = ' '.join(["%02x" % ord(x) for x in chars])
        printable = ''.join(["%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in chars])
        lines.append("%04x  %-*s  %s\n" % (c, length*3, hex, printable))
    return ''.join(lines)

def ccittcrc16(bytes, crc=0xFFFF):
  for byte in bytes:
    for i in range(0,8):
      if((crc&0x0001)^((byte>>i)&0x0001)):
        crc=(crc>>1)^0x8408
      else:
        crc=(crc>>1)
  crc=~crc
  byte=crc
  crc=((crc<<8) & 0xFF00)|((byte>>8) & 0xFF)
  return (crc & 0xFFFF)
# To call ccittcrc16 with a string, use ccittcrc16(map(ord,'string'))

#create a message sequence number that increments with every packet transmitted by the gateway
seqNum = 0
	
#get the lower 32 bits of the address of radio module in the gateway
gatewayAddress = zigbee.ddo_get_param(None,'SL')

#setup radio socket
size = 1024 
radioSocket = socket.socket(socket.AF_XBEE, socket.SOCK_DGRAM, socket.XBS_PROT_TRANSPORT) 
try:
	radioSocket.bind(("", 0xe8, 0, 0)) 
except socket.error, msg:
    print 'Failed to bind radio socket. Exception: ' + str(msg[0]) + ' - ' + msg[1]
    sys.exit()
radioSocket.setblocking(0)
#radioSocket.listen(5) 
#radioClients = [radioSocket] 
print 'Radio socket: ' + str(radioSocket.getsockname())

#setup datamanager connection
size = 1024 
PORT = 5000
etherSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
etherSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
	etherSocket.bind(('', 35333)) 
except socket.error, msg:
    print 'Failed to bind TCP port 35333. Exception: ' + str(msg[0]) + ' - ' + msg[1]
    sys.exit()


etherSocket.listen(5) 
etherClients = [etherSocket]
print 'Ethernet socket' + str(etherSocket.getsockname())



running = 1


while running: 
	inputready,outputready,exceptready = select.select([radioSocket] + etherClients,[],[]) 

	for s in inputready: 

		if s == radioSocket: 
			try:
				data,sensoraddress = s.recvfrom(size)
				if len(data) == 9 and chr(0) == data[5]: # 4 byte SN, 1 byte SeqNum, Opcode 0x00, Capabilities 0x00, Two byte CRC
					try:
						if 18191 == ccittcrc16(map(ord,data)):
							print 'Hello CRC OK'
							seqNum+=1
							txpacket = gatewayAddress + chr(seqNum % 256) + chr(1) + chr(0) + chr(0) # SeqNum, OpCode 0x01, Capabilities 0x00, Routing Metric 0
							packetcrc = ccittcrc16(map(ord,txpacket))
							txpacket = txpacket + chr((packetcrc>>8)&0xFF) + chr(packetcrc&0xFF)
							s.sendto(txpacket, sensoraddress)
							print 'Hello Sensor: ' + hex(ord(data[0])) + ' ' + hex(ord(data[1])) + ' ' + hex(ord(data[2])) + ' ' + hex(ord(data[3])) + ' XBee Addr: ' + str(sensoraddress) + ' SEQ: ' + hex(ord(data[4]))
						else:
							print 'Hello CRC Wrong: ' + hex(ord(data[-2])) + ' ' + hex(ord(data[-1])) + ' Packet Rejected'
							data = None
					except socket.error, msg:
						print 'Failed to send hello message back to sensor. Exception: ' + str(msg[0]) + ' - ' + msg[1]
				else: # Add CRC verification for all received packets
					packet = '0x'
					for i in range(0,len(data)):
						packet = packet + hex(ord(data[i]))[-2:] + ' '
					print 'RX Pkt: ' + packet
					if 18191 == ccittcrc16(map(ord,data)):
						print 'CRC OK'
					else:
						if len(data) > 3:
							print 'CRC Wrong: ' + hex(ord(data[-2])) + ' ' + hex(ord(data[-1])) + ' Packet Rejected'
						else:
							print 'CRC Wrong, Packet less than 4 bytes, Packet Rejected'
						data = None
			except socket.error, msg:
				print 'Failed to receive radio packet. Closing and removing. Exception: ' + str(msg[0]) + ' - ' + msg[1]
				print s.getsockname()
				s.close() 
				
			for eSock in etherClients:
				if eSock != etherSocket and data is not None:
					try:
						eSock.sendall(chr(0xFF) + (chr(0x00)*20) + chr(0xFF) + chr(len(data)&0xFF) + data) # 1/14/2014  Looking at ways to add header (and possibly tailer) information to packets 
					except socket.error, msg:
						print 'Failed to forward packet. Closing and removing. Exception: ' + str(msg[0]) + ' - ' + msg[1]
						eSock.close() 
						etherClients.remove(eSock)
			try:
                # following 4 lines for azure cloud
			    # client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			    # server_address=('192.168.1.143', 5000)
			    # client_socket.sendto((chr(0xFF) + (chr(0x00)*20) + chr(0xFF) + chr(len(data)&0xFF) + data),server_address)
			    # print 'transferred'

			    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			    server_address=('192.168.1.238', 5000)
			    client_socket.connect(server_address)
			    client_socket.sendall(chr(0xFF) + (chr(0x00)*20) + chr(0xFF) + chr(len(data)&0xFF) + data)
			    client_socket.close()
			except socket.error, msg:
			    print 'Failed to forward to Azure. Closing and removing. Exception: ' + str(msg[0]) + ' - ' + msg[1]
			    client_socket.close() 
#			client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#			server_address=('13.95.150.156', 5000)
#			server_address=('192.168.1.238', 5000)
#			client_socket.connect(server_address)
#			client_socket.sendall(chr(0xFF) + (chr(0x00)*20) + chr(0xFF) + chr(len(data)&0xFF) + data)
#			client_socket.close()
#			server_address=('192.168.128.238', 5000)



		elif s == etherSocket: 
			client, address = etherSocket.accept() 
			etherClients.append(client)
			print 'Added ethernet client: ' + str(address)
			
						
		elif s in etherClients:
			try:
				data = s.recv(size)
				if len(data) == 0:
					print 'Received shutdown request from ' + str(s.getpeername()) + '. Closing and removing.'
					s.close()
					etherClients.remove(s)
				else:
					print 'Received from etherClients list ' + str(s.getpeername()) + ':\n' + hexdump(data)

				if data.strip() == 'exit':
					running = 0
				elif data.strip() == 'show':
					print 'ethernet clients:'
					for sock in etherClients:
						try:
							print str(sock.getpeername())
						except socket.error:
							pass
			except socket.error, msg:
				print 'Failed to receive from etherClient. Closing and removing. Exception: ' + str(msg[0]) + ' - ' + msg[1]
				s.close() 
				etherClients.remove(s) 
				
		else:
			s.close()
				
radioSocket.close()
for s in etherClients:
	s.close()
