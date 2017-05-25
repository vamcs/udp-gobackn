import threading
import time
from socket import *
import checksum_udp

# Socket
serverName = ''
serverPort = 12000
listener_socket = socket(AF_INET, SOCK_DGRAM)

# Go-back-N
window_size = 3
base = 0
nextseqnum = 0
data = []
delim = '_'
timeout_timer = None
buffer_full = False
simulation = True


def timeout_callback():
    global timeout_timer
    print '%s: TIMEOUT: Resending: ' % time.asctime(),
    stop = False
    i = base
    while not stop and i != nextseqnum:
        listener_socket.sendto(data[i], (serverName, serverPort))
        print '%s ' % data[i],
        i = i + 1
        if i == nextseqnum:
            stop = True
    print ''
    timeout_timer = spawn_timer()
    timeout_timer.start()


def spawn_timer():
    return threading.Timer(5, lambda: timeout_callback())


def spawn():
    return threading.Thread(target=listener_callback)


def listener_callback():
    while 1:
        rcvd_data, server_address = listener_socket.recvfrom(2048)
        # new_listener = spawn()    # Consider spawning new threads at sender?
        # new_listener.start()
        receive_data(rcvd_data)


def receive_data(rcvd_data):
    print '%s: Received data: %s' % (time.asctime(), rcvd_data)
    global base
    global buffer_full
    global timeout_timer
    new_base = int(rcvd_data.split(delim)[0]) + 1
    base = new_base if new_base > base else base
    if base == nextseqnum:
        timeout_timer.cancel()
    else:
        if timeout_timer.is_alive:
            timeout_timer.cancel()
            timeout_timer = spawn_timer()
        timeout_timer.start()
    if nextseqnum - base < window_size:
        buffer_full = False


def send_data():
    global nextseqnum
    global timeout_timer
    global buffer_full
    global simulation
    print '+---------------------+'
    print '|Data can be sent now.|'
    print '+---------------------+'
    data_scripted = ['test6', 'test5', 'test4', 'test3', 'test2', 'test1', 'test0']
    while 1:
        if nextseqnum - base == window_size:
            buffer_full = True
            print '\n!------------------------!'
            print '!WARNING: Buffer is full.!'
            print '!------------------------!'
            print 'Buffer content: ',
            stop = False
            i = base
            while not stop and i != nextseqnum:
                print '%s ' % data[i],
                i = i + 1
                if i == nextseqnum:
                    stop = True
            print '\n'
        # Waits until data can be sent.
        while buffer_full:
            None
        # Follows defined 'script' to simulate errors and then accept the user's input.
        if not data_scripted or not simulation:
            message = raw_input()
        else:
            message = data_scripted.pop()
            time.sleep(1)
            if nextseqnum == 6 or nextseqnum == 5:
                time.sleep(4)
        message = nextseqnum.__str__() + delim + message
        message += delim + checksum_udp.checksum(str.encode(message)).__str__()
        # Since the buffer is checked as full at the beginning of the routine, the following can always be run:
        data.append(message)
        print '%s: Sent data: %s' % (time.asctime(), data[nextseqnum])
        listener_socket.sendto(data[nextseqnum], (serverName, serverPort))
        if base == nextseqnum:
            if timeout_timer.is_alive:
                timeout_timer.cancel()
                timeout_timer = spawn_timer()
            timeout_timer.start()
        nextseqnum = nextseqnum + 1


def main():
    global timeout_timer
    global simulation
    timeout_timer = spawn_timer()
    listener = spawn()
    listener.daemon = True
    listener.start()
    answer = raw_input('Use scripted input? (Y/N): ')
    simulation = True if answer == 'Y' or answer == 'y' else False
    if simulation:
        print 'Simulation script:'
        print 'Packet 0: \'test0\' > Normal delivery and receipt.'
        print 'Packet 1: \'test1\' > Normal delivery and receipt.'
        print 'Packet 2: \'test2\' > Delayed delivery and delayed receipt. Forces timeout of packets 2, 3 and 4.'
        print 'Packet 3: \'test3\' > Unordered packet delivery and receipt after timeout of packets 3, 4 and 5.'
        print 'Packet 4: \'test4\' > Unordered packet delivery and receipt after timeout of packets 3, 4 and 5.'
        print 'Packet 5: \'test5\' > Packet lost and receipt after timeout.'
        print 'Packet 6: \'test6\' > Packet\'s checksum is corrupted at delivery and receipt after timeout.'
        raw_input('Press enter to continue...')
    send_data()


if __name__ == "__main__":
    main()
