class DifferentialDriveController:
    def __init__(self, robot_ip, robot_port, speed_range):
        """
        Constructor for DifferentialDriveController
        @param speed_range: Speed range for the motors (0 to speed_range)
        """
        self.speed_range = speed_range
        self.robot_ip = robot_ip
        self.robot_port = robot_port

    def move(self, left_speed, right_speed):
        """
        Move robot using differential drive
        @param left_speed: Speed for left motor (-100 to 100)
        @param right_speed: Speed for right motor (-100 to 100)
        """
        if not (-self.speed_range <= left_speed <= self.speed_range and 
            -self.speed_range <= right_speed <= self.speed_range):
            raise ValueError(f"Speed must be between -{self.speed_range} and {self.speed_range}")
        
        # Implementation for WS and setting motor speeds
        pass

    def stop(self):
        """Stop both motors"""
        self.move(0, 0)
