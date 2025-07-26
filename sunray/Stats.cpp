// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

#include "Stats.h"
#include "robot.h"
#include "motor.h"
#include <Arduino.h>


unsigned long statIdleDuration = 0; // seconds
unsigned long statChargeDuration = 0; // seconds
unsigned long statMowDurationMotorRecovery = 0; // seconds
unsigned long statMowDurationInvalid = 0; // seconds
unsigned long statMowDuration = 0; // seconds
unsigned long statMowDurationFloat = 0; // seconds
unsigned long statMowDurationFix = 0; // seconds
unsigned long statMowFloatToFixRecoveries = 0; // counter
unsigned long statMowInvalidRecoveries = 0; // counter
unsigned long statImuRecoveries = 0; // counter
unsigned long statMowObstacles = 0 ; // counter
unsigned long statEscapeLawnCounter = 0 ; // MrTree counter
unsigned long statMowBumperCounter = 0; 
unsigned long statMowSonarCounter = 0;
unsigned long statMowLiftCounter = 0;
unsigned long statMowGPSMotionTimeoutCounter = 0;
unsigned long statMowGPSNoSpeedCounter = 0;
unsigned long statMowRotationTimeoutCounter = 0;
unsigned long statMowImuNoRotationSpeedCounter = 0;
unsigned long statMowDiffIMUWheelYawSpeedCounter = 0;
unsigned long statGPSJumps = 0; // counter
unsigned long statMowToFCounter = 0;
float statTempMin = 9999; 
float statTempMax = -9999; 
float statMowMaxDgpsAge = 0; // seconds
float statMowDistanceTraveled = 0; // meter


unsigned long nextStatTime = 0;
SolType lastSolution = SOL_INVALID;    


// Hilfsfunktion zum sicheren Vergleich von Zeit, auch bei Überlauf von millis()
static bool timePassed(unsigned long now, unsigned long *last, unsigned long interval) {
    if (now - *last >= interval) {
        *last = now;
        return true;
    }
    return false;
}

// Optimierte Statistikberechnung
void calcStats(){
    unsigned long now = millis();
    if (!timePassed(now, &nextStatTime, 1000)) return; // nur jede Sekunde

    switch (stateOp) {
        case OP_IDLE:
            statIdleDuration++;
            break;

        case OP_MOW:
            statMowDuration++;
            if (motor.motorRecoveryState) statMowDurationMotorRecovery++;
            if (gps.solution == SOL_FIXED) statMowDurationFix++;
            else if (gps.solution == SOL_FLOAT) statMowDurationFloat++;
            else if (gps.solution == SOL_INVALID) statMowDurationInvalid++;
            if (gps.solution != lastSolution) {
                if ((lastSolution == SOL_FLOAT) && (gps.solution == SOL_FIXED))
                    statMowFloatToFixRecoveries++;
                if (lastSolution == SOL_INVALID)
                    statMowInvalidRecoveries++;
                lastSolution = gps.solution;
            }
            statMowMaxDgpsAge = max(statMowMaxDgpsAge, (now - gps.dgpsAge)/1000.0f);
            break;

        case OP_CHARGE:
            statChargeDuration++;
            break;

        default:
            // andere Betriebszustände werden aktuell nicht gezählt
            break;
    }
}

// Beispiel für Resetten der Statistik (z.B. am Tagesanfang)
void resetStats() {
    statIdleDuration = 0;
    statChargeDuration = 0;
    statMowDurationMotorRecovery = 0;
    statMowDurationInvalid = 0;
    statMowDuration = 0;
    statMowDurationFloat = 0;
    statMowDurationFix = 0;
    statMowFloatToFixRecoveries = 0;
    statMowInvalidRecoveries = 0;
    statImuRecoveries = 0;
    statMowObstacles = 0;
    statEscapeLawnCounter = 0;
    statMowBumperCounter = 0;
    statMowSonarCounter = 0;
    statMowLiftCounter = 0;
    statMowGPSMotionTimeoutCounter = 0;
    statMowGPSNoSpeedCounter = 0;
    statMowRotationTimeoutCounter = 0;
    statMowImuNoRotationSpeedCounter = 0;
    statMowDiffIMUWheelYawSpeedCounter = 0;
    statGPSJumps = 0;
    statMowToFCounter = 0;
    statTempMin = 9999;
    statTempMax = -9999;
    statMowMaxDgpsAge = 0;
    statMowDistanceTraveled = 0;
    lastSolution = SOL_INVALID;
}


/*
// calculate statistics
void calcStats(){
  if (millis() >= nextStatTime){
    nextStatTime = millis() + 1000;
    switch (stateOp){
      case OP_IDLE:
        statIdleDuration++;
        break;
      case OP_MOW:      
        statMowDuration++;
        if (motor.motorRecoveryState) statMowDurationMotorRecovery++;
        if (gps.solution == SOL_FIXED) statMowDurationFix++;
          else if (gps.solution == SOL_FLOAT) statMowDurationFloat++;   
          else if (gps.solution == SOL_INVALID) statMowDurationInvalid++;
        if (gps.solution != lastSolution){      
          if ((lastSolution == SOL_FLOAT) && (gps.solution == SOL_FIXED)) statMowFloatToFixRecoveries++;
          if (lastSolution == SOL_INVALID) statMowInvalidRecoveries++;
          lastSolution = gps.solution;
        } 
        statMowMaxDgpsAge = max(statMowMaxDgpsAge, (millis() - gps.dgpsAge)/1000.0);        
        break;
      case OP_CHARGE:
        statChargeDuration++;
        break;
    }     
  }   
}
*/
