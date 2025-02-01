package dev.badbird;

import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;
import com.pi4j.io.pwm.Pwm;
import io.javalin.Javalin;
import io.javalin.websocket.WsContext;
import com.pi4j.Pi4J;
import com.pi4j.context.Context;
import com.pi4j.io.gpio.digital.DigitalOutput;
import com.pi4j.io.gpio.digital.DigitalState;
import io.javalin.websocket.WsMessageContext;

public class MotorControlServer {

    // Gson instance for JSON parsing
    private static final Gson gson = new Gson();
    // Our MotorController instance
    private static MotorController motorController;

    public static void main(String[] args) {
        Context pi4j = Pi4J.newAutoContext();

        motorController = new MotorController(pi4j);

        Javalin app = Javalin.create(config -> {
            config.http.defaultContentType = "application/json";
        }).start(7000);

        app.ws("/motor", ws -> {
            ws.onConnect(ctx -> System.out.println("WebSocket connected: " + ctx.getSessionId()));
            ws.onMessage(ctx -> handleMessage(ctx));
            ws.onClose(ctx -> System.out.println("WebSocket closed: " + ctx.getSessionId()));
        });
        app.get("/", ctx -> ctx.result("Motor Control Server is running."));
    }

    private static void handleMessage(WsMessageContext ctx) {
        String msg = ctx.message();
        try {
            MotorCommand command = gson.fromJson(msg, MotorCommand.class);
            if (command.motor1 < -255 || command.motor1 > 255 || command.motor2 < -255 || command.motor2 > 255) {
                ctx.send("Error: Motor values must be between -255 and 255");
                return;
            }
            motorController.setMotor1Speed(command.motor1);
            motorController.setMotor2Speed(command.motor2);
            System.out.println("Received motor command: motor1=" + command.motor1 + ", motor2=" + command.motor2);
        } catch (JsonSyntaxException e) {
            ctx.send("Error: Invalid JSON");
        }
    }

    /**
     * Class representing a motor command.
     */
    static class MotorCommand {
        int motor1;
        int motor2;
    }

    static class MotorController {
        private final DigitalOutput motorAIn1;
        private final DigitalOutput motorAIn2;
        private final Pwm motorAPwm;

        private final DigitalOutput motorBIn1;
        private final DigitalOutput motorBIn2;
        private final Pwm motorBPwm;

        public MotorController(Context pi4j) {
            motorAIn1 = pi4j.create(DigitalOutput.newConfigBuilder(pi4j)
                    .id("MotorA_IN1")
                    .name("Motor A IN1")
                    .address(17)      // BCM 17
                    .shutdown(DigitalState.LOW)
                    .initial(DigitalState.LOW)
                    .build());

            // IN2: BCM 27
            motorAIn2 = pi4j.create(DigitalOutput.newConfigBuilder(pi4j)
                    .id("MotorA_IN2")
                    .name("Motor A IN2")
                    .address(27)      // BCM 27
                    .shutdown(DigitalState.LOW)
                    .initial(DigitalState.LOW)
                    .build());

            // ENA (PWM): BCM 22
            motorAPwm = pi4j.create(Pwm.newConfigBuilder(pi4j)
                    .id("MotorA_ENA")
                    .name("Motor A ENA PWM")
                    .address(22)      // BCM 22
                    .initial(0)
                    .build());

            // --- Setup for Motor B (motor2) ---
            // IN1: BCM 23
            motorBIn1 = pi4j.create(DigitalOutput.newConfigBuilder(pi4j)
                    .id("MotorB_IN1")
                    .name("Motor B IN1")
                    .address(23)      // BCM 23
                    .shutdown(DigitalState.LOW)
                    .initial(DigitalState.LOW)
                    .build());

            // IN2: BCM 24
            motorBIn2 = pi4j.create(DigitalOutput.newConfigBuilder(pi4j)
                    .id("MotorB_IN2")
                    .name("Motor B IN2")
                    .address(24)      // BCM 24
                    .shutdown(DigitalState.LOW)
                    .initial(DigitalState.LOW)
                    .build());

            // ENB (PWM): BCM 25
            motorBPwm = pi4j.create(Pwm.newConfigBuilder(pi4j)
                    .id("MotorB_ENB")
                    .name("Motor B ENB PWM")
                    .address(25)      // BCM 25
                    .initial(0)
                    .build());
        }

        public void setMotor1Speed(int speed) {
            int pwmValue = Math.abs(speed);
            if (speed > 0) {
                motorAIn1.high();
                motorAIn2.low();
            } else if (speed < 0) {
                motorAIn1.low();
                motorAIn2.high();
            } else {
                motorAIn1.low();
                motorAIn2.low();
            }
            motorAPwm.dutyCycle(pwmValue);
        }
        public void setMotor2Speed(int speed) {
            int pwmValue = Math.abs(speed);
            if (speed > 0) {
                motorBIn1.high();
                motorBIn2.low();
            } else if (speed < 0) {
                motorBIn1.low();
                motorBIn2.high();
            } else {
                motorBIn1.low();
                motorBIn2.low();
            }
            motorBPwm.dutyCycle(pwmValue);
        }
    }
}
