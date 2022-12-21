/**********************************************************************
  Filename    : IOT Smart Keypad
  Description : IOT Smart Keypad that configures passcode on backend and sends doorbell motion data, and Admin can remotely unlock keypad from website
  Author      : Pranav Rajan
  Email       : rajan23@up.edu
  Date        : December 6 2022
**********************************************************************/
#include <WiFi.h>
#include <HTTPClient.h>
#include <Keypad.h>
#include <Wire.h>
const char * ssid = "UPIoT";
const char * password = "";
//const char* ssid = "Ayurveda";
//const char* password = "Sarinivi1";
const char* FetchConfiguredPasscode = "http://pranavrajan568.pythonanywhere.com/FetchConfiguredPasscode";
const char * FetchUnlockedStatus = "http://pranavrajan568.pythonanywhere.com/FetchUnlockedStatus";
const char * serverName = "http://pranavrajan568.pythonanywhere.com";
String myDeviceId = "94:E6:86:E1:20:DC ";

unsigned long lastTime = 0;
unsigned long timerDelay = 3000;
unsigned long lastMotionTime = 0;
unsigned long motionTimerDelay = 500;

String finalUrl;



#define PIN_BUTTON 4
#define TRIG 5
#define ECHO 18
float distance;
float duration;
float timeUltrasonic =  200 * 60;

#include <ESP32Servo.h>
#define ledPin 2
int servoAngle = 0;
int servoPin = 15;
Servo lockServo;
 

String enteredPasscode = "";
String configuredPasscode;
String current_unlocked_status = "Lock";


#define ROW_NUM     4 // four rows
#define COLUMN_NUM  4 // four columns

char keys[ROW_NUM][COLUMN_NUM] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte pin_rows[ROW_NUM] = {14,27,26, 25}; 
byte pin_column[COLUMN_NUM] = {13,21,22,23};  

Keypad keypad = Keypad( makeKeymap(keys), pin_rows, pin_column, ROW_NUM, COLUMN_NUM );







void setup() {
  
  // initialize LED, TRIG, ECHO pins 
   pinMode(ledPin,OUTPUT);
   pinMode(PIN_BUTTON, INPUT);
   pinMode(TRIG, OUTPUT);
   pinMode(ECHO,INPUT);
   
  lockServo.setPeriodHertz(50);// servo is initialized at 50 Hertz
  lockServo.attach(servoPin, 500, 2500);  
   
  Serial.begin(115200); //Set the baud rate to 115200


  // beginning the wifi connection by providing it the ssid and password
  WiFi.begin(ssid, password);
  Serial.println("Connecting");
  while(WiFi.status() != WL_CONNECTED) {
    // while it waiting to connect it will print a dot every half second
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());
  //keeps trying over the given timer delay to establish connection
  Serial.println("Timer set to " + String(timerDelay) + " miliseconds (timerDelay variable), it will take that long before publishing the first reading.");

  
}


//this method makes GET request, retreiving the information returned from a flask route
String httpGETRequest(const char* serverName) {
  HTTPClient http;
  
  finalUrl = serverName; 
  finalUrl = finalUrl;
  
  http.begin(finalUrl);
  
  int httpResponseCode = http.GET();
  
  String payload = "{}"; 

  if (httpResponseCode>0) {
    payload = http.getString();
  }
  else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
  }
  http.end();

  return payload;
}

//this method makes a POST request, sending the entered passcode by the user along with a boolean, indicating whether the entered passcode is correct or not
void sendPasscode(String entered_passcode,String correct_boolean ,const char * serverLink){
  
HTTPClient http;
String urlLink = serverLink;

//inserts the entered_passcode and correct_boolean values into the URL
urlLink = urlLink + "/" + String(entered_passcode)+"/"+String(correct_boolean);
Serial.println("This is the url link sent to " + urlLink);

http.begin(urlLink);
http.addHeader("Content-Type","text/plain");
String requestData = "Post";
//Makes POST Request at the URL
int responseCode = http.POST(requestData);

Serial.println("This is reponse code for sending passcode "+ String(responseCode));

http.end();
  
}

//this method sends motion detected at the doorbell through the ultrasonic sensor
//sends this data through a POST request to the backend
void sendMotionData(String doorbell_distance,const char * serverLink){
HTTPClient http;
String urlLink = serverLink;

//doorbell distance is embedded in url, that is called in POST request
urlLink = urlLink + "/" + String(doorbell_distance);
Serial.println("This is the url link sent to " + urlLink);

http.begin(urlLink);
http.addHeader("Content-Type","text/plain");

//POST request sent
String requestData = "Post";
int responseCode = http.POST(requestData);

Serial.println("This is reponse code for sending Motion "+ String(responseCode));

http.end();
  
  
}


//this method calculates the distance between the user and the doorbell, through utilizing the ultrasonic sensor
float ultrasonicSensor(){
    digitalWrite(TRIG,LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG,HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG,LOW);
    duration = pulseIn(ECHO,HIGH);
//calculates distance based on duration of sound wave traveling back and forth
    distance = duration * .034 / 2;

    return distance;

}

//this method turns on an LED for 3 seconds, to simulate a lock that is unlocking
void writeLED(){
 digitalWrite(ledPin,HIGH);
 delay(3000);
 digitalWrite(ledPin,LOW);
  
}


//this method rotates the servo 90 degrees, to demonstrate the unlocking of a lock
void unlockServo(){
 for(servoAngle = 0 ; servoAngle < 90 ; servoAngle += 1 ){
         lockServo.write(servoAngle);
         delay(15);
 }
 delay(1000);
                
 for(servoAngle = 90 ; servoAngle > 0 ; servoAngle -= 1 ){
         lockServo.write(servoAngle);
         delay(15);
 }
  
}  
  

//this method allows the user to enter keys to enter a passcode on the keypad
//this method validates if the user has entered the correct passcode
void keypadEnterPasscode(){
     char typedChar = keypad.getKey();

     if(typedChar){
        //if key 'A' is not typed, lets the user keep typing in the passcode
         if(typedChar != 'A'){
         enteredPasscode += typedChar;
         Serial.println("what you entered so far = " + enteredPasscode);
        

         }
        //if key 'A' is typed then then the entered passcode is checked to see if it is correct
         else if(typedChar == 'A'){
          
            //if entered passcode is correct
             if(enteredPasscode.equals(configuredPasscode)){
                //access granted
                //correct attempt sent to backend through POST request, which is then added to LoginAttemptTable in SQL Database
                //passcode reinitialized for next attempt
                //LED lights up, demonstrating unlocking
                //Servo Lock turns, demonstrating unlocking
                
                Serial.println("Accepted Access, entered Passcode =" + enteredPasscode  + " configured Passcode = " + configuredPasscode  );
                sendPasscode(enteredPasscode, "Yes", serverName);
                enteredPasscode = "";
                writeLED();
                unlockServo();
                

             }
             //if the entered passcode is incorrect
             else if(!(enteredPasscode.equals(configuredPasscode))){
              //access is not granted
              //login attempt sent to backend through POST request, which is then added to LoginAttemptTable in SQL Database
              //entered passcode reinitialized for next attempt

              Serial.println("Denied Access , entered Passcode =" + enteredPasscode  + " configured Passcode = " + configuredPasscode);
              sendPasscode(enteredPasscode,"No",serverName);
              enteredPasscode = "";
             }
    
         }
         

     }

  
}





// the loop function runs over and ovser again forever
void loop() {
  
keypadEnterPasscode();


      if ((millis() - lastTime) > timerDelay) {
        
          if(WiFi.status()== WL_CONNECTED){
            //keeps retreiving the configured passcode from the backend, on each timer delay
            configuredPasscode = httpGETRequest(FetchConfiguredPasscode);
            
            //gets the unlocked status of the lock from the backend web form
            String temp_unlocked_status = current_unlocked_status;
            current_unlocked_status = httpGETRequest(FetchUnlockedStatus);

            //if the Admin changes the status from Lock to Unlock, the LED lights up to simulate unlocking
            if(temp_unlocked_status.equals("Lock") && current_unlocked_status.equals("Unlock")){
              writeLED();
            }
            //if the Admin changes the status from Unlock to Lock, the LED lights up to simulate locking
            if(temp_unlocked_status.equals("Unlock") && current_unlocked_status.equals("Lock")){
              writeLED();
            }

                 
          }
      
          else {
            Serial.println("WiFi Disconnected");
          }
          lastTime = millis();
        }
      
      
       //at every motion timer delay
       if((millis() - lastMotionTime) > motionTimerDelay ){
             float dist = ultrasonicSensor();
             //threshold distance is 5cm
             //if distance to the doorbell is within the threshold value, then doorbell distance is sent to Flask backend
             if(dist < 5 && dist !=0){
              sendMotionData(String(dist),serverName);
             }
           
      
        lastMotionTime = millis();
       }

  
 
}
