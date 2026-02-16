#pragma once
#include <math.h>

#define NUM_LEGS 4
#define JOINTS_PER_LEG 3
#define NUM_JOINTS (NUM_LEGS * JOINTS_PER_LEG)

// for now we only use leg 0, others stay zero
void spider_compute_joint_angles(double t, double *joint_angles);
