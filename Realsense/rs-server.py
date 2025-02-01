import cv2
import logging
from npsocket import SocketNumpyArray

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


color_socket = SocketNumpyArray()
color_socket.initalize_receiver(1000)

depth_socket = SocketNumpyArray()
depth_socket.initalize_receiver(1001)
try:
    while True:
        color_frame = color_socket.receive_array()
        depth_frame = depth_socket.receive_array()

        if color_frame is not None:
            cv2.imshow("Color Frame", color_frame)
        
        if depth_frame is not None:
            cv2.imshow("Depth Frame", depth_frame)
        
        # Press Q on keyboard to exit
        if cv2.waitKey(25) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    logger.info("Shutting down...")

finally:
    cv2.destroyAllWindows()


