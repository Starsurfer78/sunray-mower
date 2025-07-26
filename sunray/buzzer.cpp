// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)


#include "buzzer.h"
#include "config.h"
#include <Arduino.h>
#include "robot.h"


void Buzzer::sound(SoundSelect idx, bool async){
  soundIdx = idx;
  toneIdx = 0;
  nextToneTime = millis();
  if (!async){
    while (nextToneTime != 0){
      run();
    }
  }
}

bool Buzzer::isPlaying(){
  return (nextToneTime != 0);
}

void Buzzer::run(){  
  if (nextToneTime == 0) return;
  unsigned long m = millis();
  if (m < nextToneTime) return;
  switch (soundIdx){
    case SND_READY:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 100; break;
        case 1: noTone();  nextToneTime = m + 100; break;
        case 2:            nextToneTime = 0;       break;
      }
      break;
    case SND_PROGRESS:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 20;  break;
        case 1: noTone();  nextToneTime = m + 20;  break;
        case 2:         	 nextToneTime = 0;      break;
      }
      break;
    case SND_OVERCURRENT:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 50;  break;
        case 1: noTone();  nextToneTime = m + 200; break;
        case 2: tone(4200); nextToneTime = m + 50;  break;
        case 3: noTone();  nextToneTime = m + 200; break;
        case 4:         	 nextToneTime = 0;       break;
      }
      break;
    case SND_WARNING:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 200;  break;
        case 1: noTone();  nextToneTime = m + 2000; break;
        case 2: tone(4200); nextToneTime = m + 200;  break;
        case 3: noTone();  nextToneTime = m + 2000; break;
				case 4: tone(4200); nextToneTime = m + 200;  break;
				case 5: noTone();  nextToneTime = m + 2000; break;
        case 6:            nextToneTime = 0;       break;
      }
      break;			
    case SND_TILT:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 100; break;
        case 1: noTone();  nextToneTime = m + 200; break;
        case 2: tone(4200); nextToneTime = m + 100; break;
        case 3: noTone();  nextToneTime = m + 200; break;
        case 4:         	 nextToneTime = 0;       break;
      }
      break;
    case SND_ERROR:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 500; break;
        case 1: noTone();  nextToneTime = m + 200; break;
        case 2: tone(4200); nextToneTime = m + 500; break;
        case 3: noTone();  nextToneTime = m + 200; break;
        case 4:            nextToneTime = 0;       break;
      }
      break;
    case SND_SOS:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 150; break;
        case 1: noTone();  nextToneTime = m + 200; break;
        case 2: tone(4200); nextToneTime = m + 150; break;
        case 3: noTone();  nextToneTime = m + 200; break;
        case 4: tone(4200); nextToneTime = m + 150; break;
        case 5: noTone();  nextToneTime = m + 200; break;
        case 6: tone(4200); nextToneTime = m + 800; break;
        case 7: noTone();  nextToneTime = m + 200; break;
        case 8: tone(4200); nextToneTime = m + 800; break;
        case 9: noTone();  nextToneTime = m + 200; break;
        case 10: tone(4200); nextToneTime = m + 800; break;
        case 11: noTone();  nextToneTime = m + 200; break;
        case 12: tone(4200); nextToneTime = m + 150; break;
        case 13: noTone();  nextToneTime = m + 200; break;
        case 14: tone(4200); nextToneTime = m + 150; break;
        case 15: noTone();  nextToneTime = m + 200; break;
        case 16: tone(4200); nextToneTime = m + 150; break;
        case 17: noTone();  nextToneTime = m + 4000; break;
        case 18:            nextToneTime = 0;       break;
      }
      break;
    case SND_WAIT:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 200; break;
        case 1: noTone();  nextToneTime = m + 800; break;
        case 2: tone(4200); nextToneTime = m + 200; break;
        case 3: noTone();  nextToneTime = m + 800; break;
        case 4:            nextToneTime = 0;       break;
      }
      break;
    case SND_GPSJUMP:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 100; break;
        case 1: noTone();  nextToneTime = m + 100; break;
        case 2: tone(4200); nextToneTime = m + 100; break;
        case 3: noTone();  nextToneTime = m + 100; break;
        case 4:            nextToneTime = 0;       break;
      }
      break;
    case SND_GPSREBOOT:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 250; break;
        case 1: noTone();  nextToneTime = m + 250; break;
        case 2: tone(3800); nextToneTime = m + 250; break;
        case 3: noTone();  nextToneTime = m + 3250; break;
        case 4:            nextToneTime = 0;       break;
      }
      break;
    case SND_GPSWAITFIX:
      switch (toneIdx){
        case 0: tone(4200); nextToneTime = m + 500; break;
        case 1: noTone();  nextToneTime = m + 250; break;
        case 2: tone(4600); nextToneTime = m + 250; break;
        case 3: noTone();  nextToneTime = m + 2000; break;
        case 4:            nextToneTime = 0;       break;
      }
      break;
    case SND_MOWSTART:
      switch (toneIdx){
        case 0: tone(3800); nextToneTime = m + 500; break;
        case 1: tone(4200);  nextToneTime = m + 500; break;
        case 2: tone(4600); nextToneTime = m + 500; break;
        case 3: tone(5000);  nextToneTime = m + 500; break;
        case 4: noTone();  nextToneTime = m + 100; break;
        case 5:            nextToneTime = 0;       break;
      }
      break;        
  }
  toneIdx++;
}

void Buzzer::begin()
{
  buzzerDriver.begin();
  toneIdx=0;
  nextToneTime=0;   
}


void Buzzer::tone( uint16_t  freq ){
  #ifdef BUZZER_ENABLE
    buzzerDriver.tone(freq);
  #endif
}


void Buzzer::noTone(){
  #ifdef BUZZER_ENABLE  
    buzzerDriver.noTone();
  #endif
}


