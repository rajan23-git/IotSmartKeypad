
# A very simple Flask Hello World app for you to get started with...

from flask import Flask,redirect, url_for, render_template,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone
oregon_timezone = timezone('US/Pacific')

app = Flask(__name__)
app.config["DEBUG"] = True
#this global boolean initializes the lock status to being locked
#detected_motion_distance and detected_motion_timestamp have not been calculated yet
unlock_boolean = "Lock"
detected_motion_distance = "not calculated yet"
detected_motion_timestamp = "not calculated yet"
#using SQLAlchemy database to store data, such as passcodes and login attempts
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="pranavrajan568",
    password="SQLPassword143",
    hostname="pranavrajan568.mysql.pythonanywhere-services.com",
    databasename="pranavrajan568$SmartLockDatabase",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
database = SQLAlchemy(app)

#this is the database model for the SQL PasscodeTable
#the table contains the fields passcode_configured and timestamp
#passcode configured is the passcode configured by the administrator and timestamp is the time it was configured
class PasscodeTable(database.Model):
    __tablename__ = "PasscodeTable"
    id = database.Column(database.Integer, primary_key = True)

    passcode_configured = database.Column(database.String(4096))
    timestamp = database.Column(database.String(4096))

#SQL database model for Login_Attempt table
#contains the fields passcode_entered, which is the passcode that the user entered on the ESP32 keypad
#the field correct_boolean indicates whether the entered passcode matched the correct passcode, and timestamp is the time when passcode was entered
class LoginAttemptTable(database.Model):
    __tablename__ = "LoginAttemptTable"
    id = database.Column(database.Integer, primary_key = True)

    passcode_entered = database.Column(database.String(4096))
    correct_boolean = database.Column(database.String(4096))
    timestamp = database.Column(database.String(4096))

#this function returns the 5 most recent login attempts from the LoginAttempt table in the SQL database
def getRecentLoginAttempts():
    login_attempts = database.session.query(LoginAttemptTable).all()
    table_size = len(login_attempts)
    recent_attempts = login_attempts[(table_size - 5) : table_size]
    return recent_attempts

#this route returns the unlocked status of the lock
#this unlocked status is fetched by the frontend ESP32 through a GET request, in order to lock or unlock the smart keypad
@app.route('/FetchUnlockedStatus')
def fetchUnlockedStatus():
    return unlock_boolean

#this route has a form, where Admin can choose to lock or unlock the smart keypad.
#the form makes a POST request to this route, and stores the unlock_boolean in a global variable.
@app.route('/UnlockDoor',methods = ["GET","POST"])
def unlockDoor():
    if(request.method == "POST"):
        global unlock_boolean
        unlock_boolean = str(request.form["UnlockDoorSelector"])
    return render_template('UnlockDoor.html',unlocked_status = unlock_boolean)


#this route receives the distance between the user and the ultrasonic sensor.
#receives this distance through a POST request made on the frontend ESP32.
#stores and timestamps this distance in a global variable
@app.route('/<doorbell_distance>',methods = ["GET","POST"])
def receiveMotion(doorbell_distance):
    if(request.method == "POST"):
        global detected_motion_distance
        global detected_motion_timestamp

        detected_motion_distance = doorbell_distance
        detected_motion_timestamp = datetime.now(oregon_timezone).strftime("%d/%m/%Y %H:%M:%S")
        print("detetced motion distance",detected_motion_distance)
        print("detected motion timestamp",detected_motion_timestamp);

    return "default return value"

#this route returns the current configured passcode
#this passcode is then fetched by the frontend ESP32 for validating passcodes entered by the user
@app.route('/FetchConfiguredPasscode')
def fetchConfiguredPasscode():
    all_entries = database.session.query(PasscodeTable).all()
    num_entries = len(all_entries)
    latest_passcode = all_entries[num_entries - 1]
    return str(latest_passcode.passcode_configured)

#this route receives login attempts from the user, on the ESP32 keypad
#receives the entered passcode, and correct boolean through a POST Request
#adds this login attempt to the LoginAttempt database table
@app.route('/<entered_passcode>/<correct_boolean>',methods = ["GET","POST"] )
def receiveLoginAttempt(entered_passcode,correct_boolean):
    if(request.method == "POST"):
        print(str(entered_passcode)+","+(correct_boolean))
        current_time = datetime.now(oregon_timezone).strftime("%d/%m/%Y %H:%M:%S")
        login_table_entry = LoginAttemptTable(passcode_entered = str(entered_passcode), correct_boolean = str(correct_boolean) , timestamp = str(current_time))
        database.session.add(login_table_entry)
        database.session.commit()

    return  "default return value"

#Displays the 5 most recent login attempts on an html webpage, and displays recent motion detected at the doorbell
#doorbell motion refers to detected distance between the user and the ultrasonic sensor
@app.route('/LoginAttempts',methods = ["GET","POST"])
def loginAttempts():

    print("default print statement")
    print(getRecentLoginAttempts())
    return render_template('LoginAttempts.html',login_attempt_array = getRecentLoginAttempts(), motion_distance = detected_motion_distance , motion_timestamp = detected_motion_timestamp )

#this route contains a form, where the administrator can enter the configured passcode, that will be used in the IOT smart keypad
#this form makes a POST request to this route, and adds the configured passcode to the PasscodeTable, in the SQL database
@app.route('/ConfigurePasscode',methods = ["GET","POST"])
def configurePasscode():
    passcode_string = "passcode not configured yet"
    if(request.method == "POST"):
        current_time = datetime.now(oregon_timezone).strftime("%d/%m/%Y %H:%M:%S")
        passcode_string = str(request.form['PasscodeTextArea']).strip()
        passcode_table_entry = PasscodeTable(passcode_configured = passcode_string,timestamp = str(current_time))
        database.session.add(passcode_table_entry)
        database.session.commit()

    return render_template('ConfigurePasscode.html', current_configured = passcode_string)





