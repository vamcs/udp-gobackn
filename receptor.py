import threading
import time
from socket import *
import checksum_udp

# Socket
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

# Go-back-N
delim = '_'
expectedseqnum = 0
corrupted_packet = False
lost_packet = False
delayed_packet = False

errors = True


def spawn():
    return threading.Thread(target=receiver_callback)


def receiver_callback():
    global expectedseqnum
    global corrupted_packet
    global delayed_packet
    global lost_packet
    data, client_address = serverSocket.recvfrom(2048)
    t = spawn()
    t.start()
    seqnum, message, cs = data.split(delim)
    checksum_msg = seqnum + delim + message
    seqnum = int(seqnum)
    # Error simulations
    if errors:
        if seqnum == 2 and not delayed_packet:      # ACK delayed forcing timeout
            delayed_packet = True
            time.sleep(10)
        if seqnum == 5 and not lost_packet:         # Packet intentionally lost
            lost_packet = True
            return
        if seqnum == 6 and not corrupted_packet:    # Packet corrupted (checksum is shifted to the left by 1 bit)
            corrupted_packet = True
            cs = (int(cs) << 1).__str__()
    print """\nData received! @ %s
    Expected sequence number: %d
    Data info:
    - Sequence Number: [%d]
    - Message: %s
    - Checksum: %s""" % (time.asctime(), expectedseqnum, seqnum, message, cs)
    if expectedseqnum == seqnum and \
        checksum_udp.checksum(str.encode(checksum_msg)).__str__() == cs:
        new_message = expectedseqnum.__str__() + delim + 'ACK'
        print '%s: Response sent: %s to %s\n' % (time.asctime(), new_message, client_address)
        serverSocket.sendto(new_message, client_address)
        expectedseqnum = expectedseqnum + 1
    else:
        print '!----------------------------------------------!'
        print '!ERROR: Corrupted or unordered packet received.!'
        print '!----------------------------------------------!'
        lastseqnum = 0 if expectedseqnum == 0 else expectedseqnum - 1
        default_message = lastseqnum.__str__() + delim + 'ACK'
        print '%s: Response sent: %s to %s\n' % (time.asctime(), default_message, client_address)
        serverSocket.sendto(default_message, client_address)


def main():
    global expectedseqnum
    global corrupted_packet
    global delayed_packet
    global lost_packet
    global errors
    answer = raw_input('Simulate errors? (Y/N): ')
    errors = True if answer == 'Y' or answer == 'y' else False
    print '+---------------------------------+'
    print '|The server is ready to receive.  |'
    print '|Type \'r\' at any time to restart. |'
    print '+---------------------------------+'
    t = spawn()
    t.start()
    while True:
        restart = raw_input()
        if restart == 'r' or restart == 'R':
            expectedseqnum = 0
            corrupted_packet = False
            delayed_packet = False
            lost_packet = False
            answer = raw_input('Simulate errors? (Y/N): ')
            errors = True if answer == 'Y' or answer == 'y' else False
            print '+----------------+'
            print '|Server restarted|'
            print '+----------------+'


if __name__ == "__main__":
    main()
