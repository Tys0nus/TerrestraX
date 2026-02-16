#include "spider_core.h"

void spider_compute_joint_angles(double t, double *q) {
  // 1) Default standing pose for all joints
  for (int i = 0; i < NUM_JOINTS; ++i)
    q[i] = 0.0;

  // Example standing pose for leg 0 (indices 0,1,2)
  q[0] = 0.0;      // coxa
  q[1] = -0.5;     // femur down
  q[2] = 1.0;      // tibia up

  // 2) Add test motion to leg 0 femur
  double amp = 0.2;           // radians
  double freq = 0.5;          // Hz
  double offset = amp * sin(2.0 * M_PI * freq * t);

  q[1] += offset;             // wiggle femur
}
