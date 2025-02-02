import json
import websocket
import threading
import time

class DifferentialDriveController:
    def __init__(self, robot_ip, robot_port, speed_range):
        print("DifferentialDriveController")
        """
        Constructor for DifferentialDriveController
        @param speed_range: Speed range for the motors (0 to speed_range)
        """
        self.speed_range = speed_range
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.ws = None
        self.connected = False
        self.connect_lock = threading.Lock()

    def on_message(self, ws, message):
        print(f"Received: {message}")

    def on_error(self, ws, error):
        print(f"Error: {error}")
        self.connected = False

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")
        self.connected = False

    def on_open(self, ws):
        print("Connection opened")
        self.connected = True

    def connect(self):
        """Establish websocket connection"""
        uri = f"ws://{self.robot_ip}:{self.robot_port}/motor"
        print(f"Connecting to {uri}")
        
        with self.connect_lock:
            if not self.connected:
                self.ws = websocket.WebSocketApp(uri,
                                               on_open=self.on_open,
                                               on_message=self.on_message,
                                               on_error=self.on_error,
                                               on_close=self.on_close)
                
                # Start the WebSocket connection in a separate thread
                wst = threading.Thread(target=self.ws.run_forever)
                wst.daemon = True
                wst.start()
                
                # Wait for connection to be established
                timeout = 5  # seconds
                start_time = time.time()
                while not self.connected and time.time() - start_time < timeout:
                    time.sleep(0.1)
                
                if not self.connected:
                    raise ConnectionError("Failed to connect to WebSocket server")

    def move(self, left_speed, right_speed):
        """
        Move robot using differential drive
        @param left_speed: Speed for left motor (-100 to 100)
        @param right_speed: Speed for right motor (-100 to 100)
        """
        print(f"Moving: Left: {left_speed}, Right: {right_speed}")
        
        if not self.connected:
            self.connect()

        # Cap the speeds to the allowed range
        left_speed = max(-self.speed_range, min(self.speed_range, left_speed))
        right_speed = max(-self.speed_range, min(self.speed_range, right_speed))
        
        json_data = {
            "command": "motor",
            "data": {
                "left": left_speed,
                "right": right_speed
            }
        }
        
        self.ws.send(json.dumps(json_data))

    def stop(self):
        """Stop both motors"""
        self.move(0, 0)

    def close(self):
        """Close the websocket connection"""
        if self.ws:
            self.ws.close()
            self.connected = False
            self.ws = None
