import cv2
import socket
import numpy as np
import signal
import sys
import select

# TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('', 5000)
sock.bind(server_address)
sock.listen(1)

# Define video writer with proper parameters
frame_width = 1280
frame_height = 720
fps = 20
fourcc = cv2.VideoWriter_fourcc(*'DIVX')
output_file = 'data/data.mp4'
writer = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

connection = None

def exit(sig, frame):
    global connection
    if connection:
        connection.close()
    cv2.destroyAllWindows()
    sock.close()
    writer.release()
    sys.exit(0)

signal.signal(signal.SIGINT, exit)

def receive_all(sock, count):
    buffer = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buffer += newbuf
        count -= len(newbuf)
    return buffer

try:
    while True:
        print("Waiting for connection...")
        readable, _, _ = select.select([sock], [], [], 1)
        if sock in readable:
            conn, addr = sock.accept()
            connection = conn
            print('Connected by', addr)
        
            while True:
                try:
                    # Read frame size
                    size_str = receive_all(conn, 16)
                    if not size_str:
                        print('Unable to retrieve frame size.')
                        break
                    size = int(size_str.strip())

                    # Read frame bytes
                    data = receive_all(conn, size)
                    if not data:
                        print('Unable to retrieve frame data.')
                        break

                    frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is None:
                        print('An error occurred while trying to decode frame bytes')
                        break

                    # Resize the frame to match the expected dimensions
                    frame = cv2.resize(frame, (frame_width, frame_height))

                    print(frame)                    
                    # Write the frame to the video file
                    writer.write(frame)

                    # Optional: Display the frame
                    # cv2.imshow('Server Frame', frame)
                    # if cv2.waitKey(1) == ord('q'):
                    #     break
                except Exception as inst:
                    print('Caught an error while trying to manage live stream.')
                    print(inst)
                    break
            connection = None
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(None, None)
finally:
    exit(None, None)
