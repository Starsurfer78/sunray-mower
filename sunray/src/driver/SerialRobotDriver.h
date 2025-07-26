// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

// Alfred mower: external robot (with motor drivers, battery, bumper etc.) connected and controlled via serial line

#ifndef SERIAL_ROBOT_DRIVER_H
#define SERIAL_ROBOT_DRIVER_H

#include <Arduino.h>
#include "RobotDriver.h"
#ifdef __linux__
  #include <Process.h>
#endif


class SerialRobotDriver: public RobotDriver {
  public:
    String robotID;
    String mcuFirmwareName;
    String mcuFirmwareVersion;
    int requestLeftPwm;
    int requestRightPwm;
    int requestMowPwm;        
    unsigned long encoderTicksLeft;
    unsigned long encoderTicksRight;
    unsigned long encoderTicksMow;
    bool mcuCommunicationLost;
    bool motorFault;
    float batteryVoltage;
    float chargeVoltage;
    float chargeCurrent;
    float mowCurr;
    float motorLeftCurr;
    float motorRightCurr;
    bool resetMotorTicks;
    float batteryTemp;
    float cpuTemp;
    bool triggeredLeftBumper;
    bool triggeredRightBumper;
    bool triggeredLift;
    bool triggeredRain;
    bool triggeredStopButton;
    // Initializes the robot driver and serial communication
    void begin() override;
    // Main loop: processes communication and controls hardware
    void run() override;
    // Returns the robot ID
    bool getRobotID(String &id) override;
    // Returns the MCU firmware version
    bool getMcuFirmwareVersion(String &name, String &ver) override;
    // Returns the CPU temperature
    float getCpuTemperature() override;
    // Sends PWM values to the motors
    void requestMotorPwm(int leftPwm, int rightPwm, int mowPwm);
    // Requests status summary from MCU
    void requestSummary();
    // Requests firmware version from MCU
    void requestVersion();
    // Updates the panel LED display
    void updatePanelLEDs();
    // Updates the CPU temperature
    void updateCpuTemperature();
    // Updates the WiFi connection state
    void updateWifiConnectionState();
    // Sets the state of a panel LED
    bool setLedState(int ledNumber, bool greenState, bool redState);
    // Turns the fan on/off
    bool setFanPowerState(bool state);
    // Turns the IMU module on/off
    bool setImuPowerState(bool state);
  protected:    
    bool ledPanelInstalled;
    #ifdef __linux__
      Process cpuTempProcess;
      Process wifiStatusProcess;    
    #endif
    String cmd;
    String cmdResponse;
    unsigned long nextMotorTime;    
    unsigned long nextSummaryTime;
    unsigned long nextConsoleTime;
    unsigned long nextTempTime;
    unsigned long nextWifiTime;
    unsigned long nextLedTime;
    int cmdMotorCounter;
    int cmdSummaryCounter;
    int cmdMotorResponseCounter;
    int cmdSummaryResponseCounter;
    // Sends a command to the MCU
    void sendRequest(String s);
    // Processes incoming serial data
    void processComm();
    // Processes a received response
    void processResponse(bool checkCrc);
    // Processes motor status response
    void motorResponse();
    // Processes status summary response
    void summaryResponse();
    // Processes firmware version response
    void versionResponse();
};

class SerialMotorDriver: public MotorDriver {
  public:
    // Initializes the motor driver
    void begin() override;
    // Main loop for motor driver
    void run() override;
    // Sets PWM values for the motors
    void setMotorPwm(int leftPwm, int rightPwm, int mowPwm) override;
    // Returns fault status of the motors
    void getMotorFaults(bool &leftFault, bool &rightFault, bool &mowFault) override;
    // Resets motor faults
    void resetMotorFaults()  override;
    // Returns current values for the motors
    void getMotorCurrent(float &leftCurrent, float &rightCurrent, float &mowCurrent) override;
    // Returns encoder ticks for the motors
    void getMotorEncoderTicks(int &leftTicks, int &rightTicks, int &mowTicks) override;
};

class SerialBatteryDriver : public BatteryDriver {
  public:
    float batteryTemp;
    bool mcuBoardPoweredOn;
    unsigned long nextTempTime;
    unsigned long nextADCTime;
    bool adcTriggered;
    unsigned long linuxShutdownTime;
    #ifdef __linux__
      Process batteryTempProcess;
    #endif
    SerialRobotDriver &serialRobot;
    SerialBatteryDriver(SerialRobotDriver &sr);
    // Initializes the battery driver
    void begin() override;
    // Main loop for battery driver
    void run() override;    
    // Returns battery voltage
    float getBatteryVoltage() override;
    // Returns charge voltage
    float getChargeVoltage() override;
    // Returns charge current
    float getChargeCurrent() override;    
    // Returns battery temperature
    float getBatteryTemperature() override;    
    // Enables/disables charging
    virtual void enableCharging(bool flag) override;
    // Keeps power on
    virtual void keepPowerOn(bool flag) override;
    // Updates battery temperature
    void updateBatteryTemperature();
};

// Common base class for simple sensor drivers
class SerialSimpleSensorDriver {
public:
    SerialRobotDriver &serialRobot;
    // Initializes the sensor driver
    SerialSimpleSensorDriver(SerialRobotDriver &sr);
    // Main loop for sensor driver
    void begin();
    void run();
    // Returns the sensor status
    bool triggered();
};

class SerialLiftSensorDriver : public SerialSimpleSensorDriver {
public:
    // Constructor for lift sensor
    SerialLiftSensorDriver(SerialRobotDriver &sr);
};

class SerialRainSensorDriver : public SerialSimpleSensorDriver {
public:
    // Constructor for rain sensor
    SerialRainSensorDriver(SerialRobotDriver &sr);
};

class SerialStopButtonDriver : public SerialSimpleSensorDriver {
public:
    // Constructor for stop button
    SerialStopButtonDriver(SerialRobotDriver &sr);
};

class SerialBumperDriver: public BumperDriver {
public:
    SerialRobotDriver &serialRobot;
    // Initializes the bumper driver
    SerialBumperDriver(SerialRobotDriver &sr);
    // Main loop for bumper driver
    void begin() override;
    void run() override;
    // Checks if an obstacle is detected
    bool obstacle() override;
    // Returns the status of the left bumper
    bool getLeftBumper() override;
    // Returns the status of the right bumper
    bool getRightBumper() override;
    // Returns both bumper statuses
    void getTriggeredBumper(bool &leftBumper, bool &rightBumper) override;
};

class SerialBuzzerDriver: public BuzzerDriver {
public:
    SerialRobotDriver &serialRobot;
    // Initializes the buzzer driver
    SerialBuzzerDriver(SerialRobotDriver &sr);
    // Main loop for buzzer driver
    void begin() override;
    void run() override;
    // Turns the buzzer off
    void noTone() override;
    // Turns the buzzer on
    void tone(int freq) override;
};


#endif