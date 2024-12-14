#include <ArduinoBLE.h>
#include <Arduino_HS300x.h>

#define VALUE_SIZE 20

BLEService temperatureService = BLEService("00000000-5EC4-4083-81CD-A10B8D5CF6EC");
BLECharacteristic temperatureCharacteristic = BLECharacteristic("00000001-5EC4-4083-81CD-A10B8D5CF6EC", BLERead | BLENotify, VALUE_SIZE);

// last temperature reading
int oldTemperature = 0;
// last time the temperature was checked in ms
long previousMillis = 0;

void setup() {
  // initialize serial communication
  Serial.begin(9600);
  while (!Serial)
    ;

  if (!HS300x.begin()) {
    Serial.println("Failed to initialize HS300x.");
    while (1)
      ;
  }

  // initialize the built-in LED pin to indicate when a central is connected
  pinMode(LED_BUILTIN, OUTPUT);

  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");

    while (1)
      ;
  }

  BLE.setLocalName("BLE-TEMP");
  BLE.setDeviceName("BLE-TEMP");
  // add the temperature characteristic
  temperatureService.addCharacteristic(temperatureCharacteristic);
  // add the service
  BLE.addService(temperatureService);
  // set initial value for this characteristic
  temperatureCharacteristic.writeValue("0.0");
  // start advertising
  BLE.advertise();

  Serial.println("Bluetooth® device active, waiting for connections...");
}

void loop() {
  // wait for a Bluetooth® Low Energy central
  BLEDevice central = BLE.central();

  // if a central is connected to the peripheral:
  if (central) {
    Serial.print("Connected to central: ");
    // print the central's BT address:
    Serial.println(central.address());
    // turn on the LED to indicate the connection
    digitalWrite(LED_BUILTIN, HIGH);


    // while the central is connected
    // update temperature every 200ms
    while (central.connected()) {
      long currentMillis = millis();
      if (currentMillis - previousMillis >= 200) {
        previousMillis = currentMillis;
        updateTemperature();
      }
    }

    // turn off the LED after disconnect
    digitalWrite(LED_BUILTIN, LOW);
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}

void updateTemperature() {
  float temperature = HS300x.readTemperature();

  if (temperature != oldTemperature) {
    char buffer[VALUE_SIZE];
    int ret = snprintf(buffer, sizeof buffer, "%f", temperature);
    if (ret >= 0) {
      temperatureCharacteristic.writeValue(buffer);
      oldTemperature = temperature;
    }
  }
}