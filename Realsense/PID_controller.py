class PIDController:
    def __init__(self, kp=0.0, ki=0.0, kd=0.0, i_zone=float('inf')):
        # PID coefficients
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.i_zone = i_zone
        
        # Internal variables
        self.prev_error = 0.0
        self.integral = 0.0
        
    def compute(self, setpoint, current_value, dt):
        """
        Compute PID control output
        dt: time step in seconds
        """
        # Calculate error
        error = setpoint - current_value
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term - only accumulate within i_zone
        if abs(error) <= self.i_zone:
            self.integral += error * dt
        i_term = self.ki * self.integral
        
        # Derivative term
        d_term = self.kd * (error - self.prev_error) / dt
        
        # Update previous error
        self.prev_error = error
        
        # Calculate total output
        output = p_term + i_term + d_term
        return output
    
    def reset(self):
        """Reset internal state of the controller"""
        self.prev_error = 0.0
        self.integral = 0.0
        
    def set_gains(self, kp, ki, kd):
        """Update PID gains"""
        self.kp = kp
        self.ki = ki
        self.kd = kd

    def set_i_zone(self, i_zone):
        """Update I-zone threshold"""
        self.i_zone = i_zone