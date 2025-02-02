import json
import websocket

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

    def connect(self):
        """Establish websocket connection"""
        uri = f"ws://{self.robot_ip}:{self.robot_port}/motor"

        print(f"Connecting to {uri}")
        self.ws = websocket.WebSocket()
        self.ws.connect(uri)

    def move(self, left_speed, right_speed):
        """
        Move robot using differential drive
        @param left_speed: Speed for left motor (-100 to 100)
        @param right_speed: Speed for right motor (-100 to 100)
        """
        print(f"Moving: Left: {left_speed}, Right: {right_speed}")
        if not self.ws:
            self.connect()
        
        # Check if websocket connection is established
        try:
            self.ws.ping()
        except:
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
            self.ws = None
