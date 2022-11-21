
# A very simple Flask Hello World app for you to get started with...

from flask import Flask,redirect, url_for, render_template,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone
oregon_timezone = timezone('US/Pacific')

app = Flask(__name__)
app.config["DEBUG"] = True

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
class PasscodeTable(database.Model):
    __tablename__ = "PasscodeTable"
    id = database.Column(database.Integer, primary_key = True)

    passcode_configured = database.Column(database.String(4096))
    timestamp = database.Column(database.String(4096))

class LoginAttemptTable(database.Model):
    __tablename__ = "LoginAttemptTable"
    id = database.Column(database.Integer, primary_key = True)

    passcode_entered = database.Column(database.String(4096))
    correct_boolean = database.Column(database.String(4096))
    timestamp = database.Column(database.String(4096))


def getConfiguredPasscode():
    all_entries = database.session.query(PasscodeTable).all()
    num_entries = len(all_entries)
    latest_passcode = all_entries[num_entries - 1]
    return latest_passcode.passcode_configured





@app.route('/PasscodeFromFrontend',methods = ["GET","POST"])
def passcodeFromFrontend():
    if(request.method == "POST"):
        passcode_data = request.get_json()
        passcode_value = passcode_data["passcode_value"]
        boolean_value = passcode_data["boolean_value"]
        current_time = datetime.now(oregon_timezone).strftime("%d/%m/%Y %H:%M:%S")

        login_table_entry = LoginAttemptTable(passcode_entered = passcode_value, correct_boolean = boolean_value , timestamp = current_time)
        database.session.add(login_table_entry)
        database.session.commit()



@app.route('/<doorbell_distance>',methods = ["GET","POST"])
def receiveMotion(doorbell_distance):
    if(request.method == "POST"):
        global detected_motion_distance
        global detected_motion_timestamp

        detected_motion_distance = doorbell_distance
        detected_motion_timestamp = datetime.now(oregon_timezone).strftime("%d/%m/%Y %H:%M:%S")
        print("detetced motion distance",detected_motion_distance)
        print("detected motion timestamp",detected_motion_timestamp);

    return "hello world"


@app.route('/FetchConfiguredPasscode')
def fetchConfiguredPasscode():
    all_entries = database.session.query(PasscodeTable).all()
    num_entries = len(all_entries)
    latest_passcode = all_entries[num_entries - 1]
    return str(latest_passcode.passcode_configured)

@app.route('/<entered_passcode>/<correct_boolean>',methods = ["GET","POST"] )
def receiveLoginAttempt(entered_passcode,correct_boolean):
    if(request.method == "POST"):
        print(str(entered_passcode)+","+(correct_boolean))
        current_time = datetime.now(oregon_timezone).strftime("%d/%m/%Y %H:%M:%S")
        login_table_entry = LoginAttemptTable(passcode_entered = str(entered_passcode), correct_boolean = str(correct_boolean) , timestamp = str(current_time))
        database.session.add(login_table_entry)
        database.session.commit()

    return  "hello world"


@app.route('/LoginAttempts',methods = ["GET","POST"])
def loginAttempts():

    print("hello world")
    return render_template('LoginAttempts.html')

@app.route('/ConfigurePasscode',methods = ["GET","POST"])
def configurePasscode():

    if(request.method == "GET"):
        return render_template('ConfigurePasscode.html')
    if(request.method == "POST"):
        current_time = datetime.now(oregon_timezone).strftime("%d/%m/%Y %H:%M:%S")
        passcode_string = str(request.form['PasscodeTextArea']).strip()
        passcode_table_entry = PasscodeTable(passcode_configured = passcode_string,timestamp = str(current_time))
        database.session.add(passcode_table_entry)
        database.session.commit()
        return render_template('ConfigurePasscode.html')
    return render_template('ConfigurePasscode.html')




