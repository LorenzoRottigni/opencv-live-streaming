import cv2
import socket
import numpy as np
import signal
import sys
import select
from yolo import yolo_detection
from datetime import datetime

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
writer = None
connection = None

def exit(sig,frame):
    global connection
    if connection:
        connection.close()
    cv2.destroyAllWindows()
    sock.close()
    if writer and writer.isOpened():
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
        if writer:
            print('Releasing writer...')
            writer.release()
            writer = None
        if sock in readable:
            if writer is None:
                filename = f"rec-{datetime.now().strftime('%H_%M_%S-%m-%d-%Y')}.mp4"
                print(f"Creating a new VideoWriter for data/{filename}...")
                writer = cv2.VideoWriter(
                    f"data/{filename}",
                    fourcc,
                    fps,
                    (frame_width, frame_height)
                )
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


                    (yolo_frame, yolo_status) = yolo_detection(frame)

                    # Write the frame to the video file
                    if writer:
                        print('Writing...')
                        writer.write(yolo_frame if yolo_status is not None else frame)
                except Exception as inst:
                    print('Caught an error while trying to manage live stream.')
                    print(inst)
                    break
            connection = None
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    exit(None, None)
