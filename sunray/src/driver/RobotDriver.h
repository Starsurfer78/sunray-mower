// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

// motor driver base, battery driver base, bumper driver base

#ifndef ROBOT_DRIVER_H
#define ROBOT_DRIVER_H

#include "../../gps.h"
#include <Client.h>

// Abstract base class for robot drivers
class RobotDriver {
  public:    
    // ---- led states -----           
    bool ledStateWifiInactive;
    bool ledStateWifiConnected;
    bool ledStateGpsFix;
    bool ledStateGpsFloat;
    bool ledStateShutdown;
    bool ledStateError;
    // Initializes the robot driver
    virtual void begin() = 0;
    // Main loop for robot driver
    virtual void run() = 0;
    // Returns the robot ID
    virtual bool getRobotID(String &id) = 0;
    // Returns the MCU firmware version
    virtual bool getMcuFirmwareVersion(String &name, String &ver) = 0;    
    // Returns the CPU temperature
    virtual float getCpuTemperature() = 0;
};

// Abstract base class for motor drivers
class MotorDriver {
  public:    
    // Initializes the motor driver
    virtual void begin() = 0;
    // Main loop for motor driver
    virtual void run() = 0;
    // Sets PWM (0-255), positive: forward, negative: backwards
    virtual void setMotorPwm(int leftPwm, int rightPwm, int mowPwm) = 0;
    // Returns motor faults
    virtual void getMotorFaults(bool &leftFault, bool &rightFault, bool &mowFault) = 0;
    // Resets motor faults
    virtual void resetMotorFaults() = 0;
    // Returns motor currents (ampere)
    virtual void getMotorCurrent(float &leftCurrent, float &rightCurrent, float &mowCurrent) = 0;
    // Returns motor encoder ticks
    virtual void getMotorEncoderTicks(int &leftTicks, int &rightTicks, int &mowTicks) = 0; 
};

// Abstract base class for battery drivers
class BatteryDriver {
  public:    
    // Initializes the battery driver
    virtual void begin() = 0;
    // Main loop for battery driver
    virtual void run() = 0;
    // Returns battery voltage
    virtual float getBatteryVoltage() = 0;
    // Returns battery temperature (degC) 
    virtual float getBatteryTemperature() = 0;
    // Returns charge voltage
    virtual float getChargeVoltage() = 0;
    // Returns charge current (amps)
    virtual float getChargeCurrent() = 0;
    // Enables battery charging
    virtual void enableCharging(bool flag) = 0;
    // Keeps system on or powers off
    virtual void keepPowerOn(bool flag) = 0;   
};

// Abstract base class for bumper drivers
class BumperDriver {
  public:    
    // Initializes the bumper driver
    virtual void begin() = 0;
    // Main loop for bumper driver
    virtual void run() = 0;
    // Checks if an obstacle is detected
    virtual bool obstacle() = 0;
    // Returns the status of the left bumper
    virtual bool getLeftBumper() = 0;
    // Returns the status of the right bumper
    virtual bool getRightBumper() = 0;
    // Returns both bumper statuses
    virtual void getTriggeredBumper(bool &leftBumper, bool &rightBumper) = 0;   
};

// Abstract base class for stop button drivers
class StopButtonDriver {
  public:    
    // Initializes the stop button driver
    virtual void begin() = 0;
    // Main loop for stop button driver
    virtual void run() = 0;
    // Returns the status of the stop button
    virtual bool triggered() = 0;   
};

// Abstract base class for lift sensor drivers
class LiftSensorDriver {
  public:    
    // Initializes the lift sensor driver
    virtual void begin() = 0;
    // Main loop for lift sensor driver
    virtual void run() = 0;
    // Returns the status of the lift sensor
    virtual bool triggered() = 0;   
};

// Abstract base class for rain sensor drivers
class RainSensorDriver {
  public:    
    // Initializes the rain sensor driver
    virtual void begin() = 0;
    // Main loop for rain sensor driver
    virtual void run() = 0;
    // Returns the status of the rain sensor
    virtual bool triggered() = 0;   
};

// Abstract base class for IMU drivers
class ImuDriver {
  public:
    float quatW; // quaternion
    float quatX; // quaternion
    float quatY; // quaternion
    float quatZ; // quaternion        
    float roll; // euler radiant
    float pitch; // euler radiant
    float yaw;   // euler radiant
    float heading; //MrTree Compass direction, try getting more Information of MPU
    float ax; //MrTree x-Acceleration of IMU
    float ay; //MrTree y-Acceleration of IMU
    float az; //MrTree z-Acceleration of IMU
    bool imuFound;   
    // Detects the IMU module (should update member 'imuFound')
    virtual void detect() = 0;             
    // Starts the IMU module with update rate 5 Hz (should return true on success)
    virtual bool begin() = 0;    
    // Main loop for IMU driver
    virtual void run() = 0;
    // Checks if data has been updated (should update members roll, pitch, yaw)
    virtual bool isDataAvail() = 0;
    // Resets module data queue (should reset module FIFO etc.)         
    virtual void resetData() = 0;        
};

// Abstract base class for buzzer drivers
class BuzzerDriver {
  public:    
    // Initializes the buzzer driver
    virtual void begin() = 0;
    // Main loop for buzzer driver
    virtual void run() = 0;
    // Turns the buzzer off
    virtual void noTone() = 0;   
    // Turns the buzzer on
    virtual void tone(int freq) = 0;
};

// Abstract base class for GPS drivers
class GpsDriver {
  public:
    unsigned long iTOW; //  An interval time of week (ITOW), ms since Saturday/Sunday transition
    int numSV;         // #signals tracked 
    int numSVdgps;     // #signals tracked with DGPS signal
    double lon;        // deg
    double lat;        // deg
    double height;     // m
    float relPosN;     // m
    float relPosE;     // m
    float relPosD;     // m
    float heading;     // rad
    float groundSpeed; // m/s
    float accuracy;    // m
    float hAccuracy;   // m
    float vAccuracy;   // m
    SolType solution;    
    bool solutionAvail; // should bet set true if received new solution 
    unsigned long dgpsAge;
    unsigned long chksumErrorCounter;
    unsigned long dgpsChecksumErrorCounter;
    unsigned long dgpsPacketCounter;
    int year;          // UTC time year (1999..2099)
    int month;         // UTC time month (1..12)
    int day;           // UTC time day (1..31)
    int hour;          // UTC time hour (0..23)
    int mins;          // UTC time minute (0..59)
    int sec;           // UTC time second (0..60) (incl. leap second)
    int dayOfWeek;     // UTC dayOfWeek (0=Monday)
    // Starts TCP receiver
    virtual void begin(Client &client, char *host, uint16_t port) = 0;
    // Starts serial receiver          
    virtual void begin(HardwareSerial& bus,uint32_t baud) = 0;
    // Main loop for GPS driver
    virtual void run() = 0;    
    // Configures the receiver    
    virtual bool configure() = 0; 
    // Reboots the receiver
    virtual void reboot() = 0;

    // Decodes iTOW into hour, min, sec and dayOfWeek(0=Monday)
    virtual void decodeTOW();
};

inline void GpsDriver::decodeTOW() {
    long towMin = iTOW / 1000 / 60;  // convert milliseconds to minutes since GPS week start
    dayOfWeek = ((towMin / 1440)+6) % 7; // GPS week starts at Saturday/Sunday transition
    unsigned long totalMin = towMin % 1440; // total minutes of current day
    hour = totalMin / 60;
    mins = totalMin % 60;
}

#endif

