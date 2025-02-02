import json
import asyncio
import websockets

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

    async def connect(self):
        """Establish websocket connection"""
        uri = f"ws://{self.robot_ip}:{self.robot_port}/motor"

        print(f"Connecting to {uri}")
        self.ws = await websockets.connect(uri)

    async def move(self, left_speed, right_speed):
        """
        Move robot using differential drive
        @param left_speed: Speed for left motor (-100 to 100)
        @param right_speed: Speed for right motor (-100 to 100)
        """
        print(f"Moving: Left: {left_speed}, Right: {right_speed}")
        if not self.ws:
            await self.connect()
        
        # Check if websocket connection is established
        if not self.ws.open:
            await self.connect()



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
        
        await self.ws.send(json.dumps(json_data))

    async def stop(self):
        """Stop both motors"""
        await self.move(0, 0)

    async def close(self):
        """Close the websocket connection"""
        if self.ws:
            await self.ws.close()
            self.ws = None
