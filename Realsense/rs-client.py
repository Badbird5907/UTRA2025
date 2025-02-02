import pyrealsense2 as rs
import numpy
from io import BytesIO
from npsocket import SocketNumpyArray
import socket
from globals import *

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, resolution_x, resolution_y, rs.format.z16, 60)
config.enable_stream(rs.stream.color, resolution_x, resolution_y, rs.format.bgr8, 60)
pipeline.start(config)

hole_filling = rs.hole_filling_filter(2)
temporal = rs.temporal_filter()
spatial = rs.spatial_filter()


colorizer = rs.colorizer()

# align depth and color frames
align_to = rs.stream.color
align = rs.align(align_to)

color_socket = SocketNumpyArray()
depth_socket = SocketNumpyArray()

color_socket.initialize_sender('localhost', 1000)
depth_socket.initialize_sender('localhost', 1001)

try:
    while True:
        frames = pipeline.wait_for_frames()
        frames = align.process(frames)
        
        depth_frame = frames.get_depth_frame()
        depth_frame = hole_filling.process(depth_frame)
        depth_frame = temporal.process(depth_frame)
        depth_frame = spatial.process(depth_frame).as_depth_frame()
        if not depth_frame:
            continue
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        color_image = numpy.asanyarray(color_frame.get_data())
        depth_map = numpy.asanyarray(depth_frame.get_data())

        

        color_socket.send_numpy_array(color_image)
        depth_socket.send_numpy_array(depth_map)   
finally:
    pipeline.stop()
