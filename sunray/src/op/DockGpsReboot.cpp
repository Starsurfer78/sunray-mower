// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

#include "op.h"
#include <Arduino.h>
#include "../../robot.h"
#include "../../map.h"

String DockGpsRebootOp::name(){
    return "DockGpsReboot";
}

void DockGpsRebootOp::begin(){
    // GPS Reboot undocking and docking
    CONSOLE.println("Rebooting GPS Module");
    // reset the flag
    maps.shouldGpsReboot = false;    
    motor.setMowState(false);
    gps.reboot();
    rebootGpsTime = millis() + DOCK_GPS_REBOOT_TIME; // wait 30 secs after reboot, then try another map routing
}


void DockGpsRebootOp::end(){
}


void DockGpsRebootOp::run(){
    battery.resetIdle();
    if (!buzzer.isPlaying()) buzzer.sound(SND_GPSREBOOT, true);
    if ((millis() > rebootGpsTime) && (gps.solution == SOL_FIXED)){
        // restart current operation from new position (restart path planning)
        CONSOLE.println("Got FIX after rebooting GPS, continuing... ");
        rebootGpsTime = 0;
        //motor.stopImmediately(false);
        //motor.setMowState(true);
        buzzer.sound(SND_READY, true);
        changeOp(*nextOp);    // restart current operation      
    }
}

