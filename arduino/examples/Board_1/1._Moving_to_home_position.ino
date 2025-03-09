#include <Braccio.h>
#include <Servo.h>

#define SOFT_START_LEVEL -70

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_rot;
Servo wrist_ver;
Servo gripper;

#include <Braccio.h>
void setup() {
  Braccio.begin(SOFT_START_LEVEL); // Initialize the Braccio
  Braccio.ServoMovement(20, 90, 90, 90, 90, 90, 90); // All servos to neutral angles
}
void loop() {}
