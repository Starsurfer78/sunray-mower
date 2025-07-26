// Ardumower Sunray
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

#include "bumper.h"
#include "config.h"
#include "robot.h"
#include <Arduino.h>

/*
  Bumper input and output state variables:
  - inputLeftPressed / inputRightPressed:  Raw input from bumper sensors (updated each run).
  - outputLeftPressed / outputRightPressed: Debounced and delayed output signals for bumper logic.
  - bumperLeft / bumperRight:  Internal state to detect state changes (edge detection).
  - leftTrigTime / rightTrigTime:  Timestamp when bumper was first pressed (for delay logic).
  - leftOnTimer / rightOnTimer:  Accumulated time bumper has been pressed (for stuck detection).
  - lastBumperTime:  Last time the bumper logic was processed (for timing calculations).
*/
volatile bool inputLeftPressed = false;
volatile bool inputRightPressed = false;

volatile bool outputLeftPressed = false;
volatile bool outputRightPressed = false;

static bool bumperLeft = false;
static bool bumperRight = false;

unsigned long leftTrigTime = 0;  // on delay timer (BUMPER_TRIGGER_DELAY) for the bumper inputs
unsigned long rightTrigTime = 0; // on delay timer (BUMPER_TRIGGER_DELAY) for the bumper inputs
unsigned long rightOnTimer = 0;  // on delay timer (BUMPER_TRIGGER_DELAY) for the bumper inputs
unsigned long leftOnTimer = 0;   // on delay timer (BUMPER_TRIGGER_DELAY) for the bumper inputs
unsigned long lastBumperTime = 0;

void Bumper::begin()
{
  bumperDriver.begin();
}

void Bumper::run()
{
  // Update bumper driver hardware and read raw bumper input states
  bumperDriver.run();
  inputLeftPressed = bumperDriver.getLeftBumper();
  inputRightPressed = bumperDriver.getRightBumper();

  if (BUMPER_ENABLE)
  {
    // Debounce and delay logic for left bumper
    if (inputLeftPressed)
    {
      if (!bumperLeft)
      { // On rising edge: store trigger time and reset timer
        leftTrigTime = millis();
        leftOnTimer = 0;
      }
      bumperLeft = true;
      leftOnTimer += millis() - lastBumperTime; // Accumulate time pressed for stuck detection
      if (millis() >= leftTrigTime + BUMPER_TRIGGER_DELAY)
        outputLeftPressed = true; // Only set output after trigger delay
    }
    else
    {
      bumperLeft = false;
      outputLeftPressed = false;
    }

    // Debounce and delay logic for right bumper
    if (inputRightPressed)
    {
      if (!bumperRight)
      { // On rising edge: store trigger time and reset timer
        rightTrigTime = millis();
        rightOnTimer = 0;
      }
      bumperRight = true;
      rightOnTimer += millis() - lastBumperTime; // Accumulate time pressed for stuck detection
      if (millis() >= rightTrigTime + BUMPER_TRIGGER_DELAY)
        outputRightPressed = true; // Only set output after trigger delay
    }
    else
    {
      bumperRight = false;
      outputRightPressed = false;
    }

    // Stuck detection: if either bumper is held too long, trigger error
    if (bumperRight || bumperLeft)
    {
      if (max(leftOnTimer, rightOnTimer) > max(leftTrigTime, rightTrigTime) + BUMPER_MAX_TRIGGER_TIME * 1000)
      {
        if (stateOp != OP_ERROR)
        {
          stateSensor = SENS_BUMPER;
          CONSOLE.println("ERROR BUMPER BLOCKED - BUMPER_MAX_TRIGGER_TIME exceeded. See config.h for further information");
          CONSOLE.print("leftBumper triggered for: ");
          CONSOLE.print(leftOnTimer);
          CONSOLE.print(" ms, rightBumper triggered for: ");
          CONSOLE.print(rightOnTimer);
          CONSOLE.println(" ms");
          setOperation(OP_ERROR);
          leftTrigTime = 0;
          rightTrigTime = 0;
          leftOnTimer = 0;
          rightOnTimer = 0;
        }
      }
    }
    lastBumperTime = millis(); // Update last processed time
    //} else {
    //  outputLeftPressed = false;
    //  outputRightPressed = false;
  }
}

bool Bumper::obstacle()
{
  if (BUMPER_ENABLE)
  {
    return (outputLeftPressed || outputRightPressed);
  }
  else
    return false;
}

bool Bumper::obstacleLeft()
{
  if (BUMPER_ENABLE)
  {
    return (outputLeftPressed);
  }
  else
    return false;
}

bool Bumper::obstacleRight()
{
  if (BUMPER_ENABLE)
  {
    return (outputRightPressed);
  }
  else
    return false;
}

// send separated signals without delay to sensortest
bool Bumper::testLeft()
{
  return (inputLeftPressed);
}

bool Bumper::testRight()
{
  return (inputRightPressed);
}
