#include <Braccio.h>
#include <Servo.h>

#define SOFT_START_LEVEL -70

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_rot;
Servo wrist_ver;
Servo gripper;

void setup() {
  //Initialization functions and set up the initial position for Braccio
  //All the servo motors will be positioned in the "safety" position:
  //Base (M1):90 degrees
  //Shoulder (M2): 45 degrees
  //Elbow (M3): 180 degrees
  //Wrist vertical (M4): 180 degrees
  //Wrist rotation (M5): 90 degrees
  //gripper (M6): 10 degrees
  Braccio.begin(SOFT_START_LEVEL);
}

void loop() {
  for (int angle = 90; angle <= 135; angle += 5) {
    Braccio.ServoMovement(20, angle, angle, 90, 90, 90, 90);
    delay(500);
  }
  for (int angle = 135; angle >= 90; angle -= 5) {
    Braccio.ServoMovement(20, angle, angle, 90, 90, 90, 90);
    delay(500);
  }
}
