import cv2
import socket
import sys
import signal

cap = cv2.VideoCapture(0)
frame_width = 1280
frame_height = 720

# TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 5000)
sock.connect(server_address)

def exit(sig,frame):
    cap.release()
    cv2.destroyAllWindows()
    sock.close()
    sys.exit(0)

signal.signal(signal.SIGINT, exit)

def live_stream(frame):
    try:
        # Resize the frame
        frame = cv2.resize(frame, (frame_width, frame_height))
        
        # JPEG frame encoding
        ret, jpeg_data = cv2.imencode('.jpg', frame)
        if not ret:
            print('Failed to encode frame.')
            return
        
        # Convert the encoded frame to bytes
        image_bytes = jpeg_data.tobytes()
        
        # Send size of the frame
        size = len(image_bytes)
        size_str = str(size).ljust(16).encode('utf-8')
        sock.sendall(size_str)
        
        # Send frame bytes
        sock.sendall(image_bytes)
    except Exception as e:
        print('An error occurred while trying to stream live video.')
        print(e)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error capturing video!")
            break

        live_stream(frame)
except Exception as e:
    print('An error occurred while capturing live streaming from the camera.')
    print(e)
finally:
    exit(None, None)
