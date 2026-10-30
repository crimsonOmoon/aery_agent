/*
  Read Temperature and Humidity
  DHT11 Library
  Author: Bonezegei (Jofel Batutay)
  Date : November 2023

  Tested using ESP32-WROOM32
*/

#include <Bonezegei_DHT11.h>

//param = DHT11 signal pin
Bonezegei_DHT11 dht(2);

void setup() {
  Serial.begin(115200);
  dht.begin();
}

void loop() {

  if (dht.getData()) {                         // get All data from DHT11
    float tempDeg = dht.getTemperature();      // return temperature in celsius
    float tempFar = dht.getTemperature(true);  // return temperature in fahrenheit if true celsius of false
    int hum = dht.getHumidity();               // return humidity
    String str  = "Temperature: ";
           str += tempDeg;
           str += "°C  ";
           str += tempFar;
           str += "°F  Humidity:";
           str += hum;
    Serial.println(str.c_str());
    //Serial.printf("Temperature: %0.1lf°C  %0.1lf°F Humidity:%d \n", tempDeg, tempFar, hum);
  }
  delay(2000);  //delay atleast 2 seconds for DHT11 to read tha data
}
