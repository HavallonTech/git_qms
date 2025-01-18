from flask import Flask, request, render_template, redirect, session, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
# configure SQL_Alchemy to work with Flask
app.secret_key = "Cisco@2025_BTHDC"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bthdcictapp.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] =False
db = SQLAlchemy(app)
# with this your db should be created and should be running effectively

#database tables to be created for the first instance
class Btqueue(db.Model):  # Capitalize 'Btqueue' to follow naming conventions
    __tablename__ = 'btqueue'
    queue_id = db.Column(db.Integer, primary_key=True)
    pat_phone = db.Column(db.String(100))
    pat_procedure = db.Column(db.String(100))
    queue_time = db.Column(db.Integer)
    service_status =db.Column(db.Integer)
    departure_time = db.Column(db.DateTime, default=datetime.utcnow)
    arrival_time = db.Column(db.DateTime, default=datetime.utcnow)
    pat_id = db.Column(db.String(100))

    def __init__(self, pat_phone, pat_procedure, pat_id, queue_time, service_status, arrival_time, departure_time):
        self.pat_phone = pat_phone
        self.pat_procedure = pat_procedure
        self.pat_id = pat_id
        self.queue_time = queue_time
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.service_status=service_status
# New database table: btdepartment
class BTDepartment(db.Model):
    dept_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dept_name = db.Column(db.String(100), nullable=False)

# New database table: btprocedures
class BTProcedures(db.Model):
    procedure_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    procedure_name = db.Column(db.String(100), nullable=False)

class appusers(db.Model):
    userid=db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    userfirstname = db.Column(db.String(50))
    userlastname = db.Column(db.String(60))
    userdepartment =db.Column(db.Integer)


    def set_password(self, userpassword):
        self.password_hash = generate_password_hash(userpassword)

    def check_password(self, userpassword):
        return check_password_hash(self.password_hash, userpassword)

#Run and create all Database tables
#Ok
with app.app_context():
        db.create_all()
#pages are created below

@app.route("/")
def index():
    if "username" in session:
        return redirect (url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username=request.form["username"]
    userpass = request.form["userpass"]
    user = appusers.query.filter_by(username=username).first()
    if user and user.check_password(userpass):
        session['username']=username
        return redirect(url_for("dashboard", username=session['username']))
    else:
        return render_template("index.html")

    
@app.route("/signup", methods=["POST"])
def signup():
    fusername=request.form["username"]
    userpass = request.form["userpass"]
    ffirstname = request.form["firstname"]
    flastname = request.form["lastname"]
    fuserdept = request.form["dept"]
    user = appusers.query.filter_by(username=fusername).first()
    if user:
        # User already exists
        return render_template("register.html", error="User already exists!")
    
    #register the user
    newuser = appusers(username=fusername, userfirstname=ffirstname, userlastname=flastname, userdepartment=fuserdept)
    newuser.set_password(userpass)
    db.session.add(newuser)
    db.session.commit()
    session['username']=fusername
    return redirect(url_for("dashboard", username=session['username']))


@app.route('/register')
def register():
    return render_template('register.html')


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("index"))
    all_data = Btqueue.query.filter_by(service_status = 1).all()
    return render_template('dashboard.html', system_queue=all_data)



@app.route('/insert', methods=["POST"])
def insert():
    if request.method == "POST":
        pat_phone = request.form['patient_phone']
        pat_id = request.form['patient_id']
        queue_time = request.form['queue_time']
        pat_procedure = request.form['patient_procedure']

        # Add the new patient record to the database
        #service_status = 1
        arrival_time = datetime.now()
        departure_time = datetime.now()
        new_patient = Btqueue(pat_phone=pat_phone, arrival_time=arrival_time , pat_procedure=pat_procedure, departure_time=departure_time , pat_id=pat_id, queue_time =queue_time, service_status=1 )
        db.session.add(new_patient)
        db.session.commit()
        flash("Patient Added Successfully")
        # Return to Index
        return redirect('/')
    
#python code to Update patient status record to either saved or not
@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    queue_id = data.get('queue_id')
    status = data.get('status')
    #print("pat_id")
    #exit()
    # Update the database
    try:
        patient = Btqueue.query.filter_by(queue_id=queue_id).first()
        if patient is None:
            print("Patient not found")
            patient = Btqueue.query.get(queue_id)
            # Perform the update
            # Check if patient exists
            return jsonify({'success': False, 'message': 'Patient not found'}), 404
        # Update service status
        patient.service_status = 2 if status == 'served' else 0
        patient.departure_time = datetime.now() 
        db.session.commit()
        print("Status updated successfully")  # Debugging line
        
        return jsonify({'success': True})
    except Exception as e:
            print(f"Error updating status: {e}")
            db.session.rollback()  # Rollback in case of error
            return jsonify({'success': False}), 500
        
@app.route('/update', methods=['POST','GET'])
def update():
        if request.method == 'POST':
            mydata = Btqueue.query.get(request.form.get('queue_id'))
            mydata.pat_phone = request.form['patient_phone']
            mydata.pat_id = request.form['patient_id']
            mydata.queue_time = request.form['queue_time']
            mydata.pat_procedure = request.form['Patient_procedure']

            db.session.commit()
            flash("Patient Record successfully Updated")
            return redirect('/')

#deleting patient from queue
@app.route('/delete/<int:queue_id>/', methods=['POST', 'GET'])
def delete(queue_id):
    if request.method == 'POST':
        queue_id = request.form.get('queue_id')
        mydata = Btqueue.query.get(queue_id)
        if mydata:
            db.session.delete(mydata)
            db.session.commit()
            flash("Record successfully deleted", 'success')
        else:
            flash("Record not found", 'warning')
    if request.method == 'GET':
        try:
            # Fetch the record by ID
            mydata = Btqueue.query.get(queue_id)
        
            # Check if the record exists
            if mydata:
                # Delete the record
                db.session.delete(mydata)
                db.session.commit()
                flash("Record successfully deleted", 'success')
            else:
                flash("Record not found", 'warning')
        except Exception as e:
            flash(f"Error deleting record: {e}", 'danger')
            flash("Record Successfully Deleted using GET")
    return redirect('/')

@app.route('/xrayview')
def xray_view():
    xray_data = Btqueue.query.filter_by(pat_procedure="X-Ray", service_status=1).all()
    return render_template('xrayview.html', xray_data=xray_data)

@app.route('/mriview')
def mriview():
    mri_data = Btqueue.query.filter_by(pat_procedure="MRI", service_status=1).all()
    return render_template('mriview.html', mri_data=mri_data)

@app.route('/ctview')
def ctview():
    ct_data = Btqueue.query.filter_by(pat_procedure="CT", service_status=1).all()
    return render_template('ctview.html', ct_data=ct_data)

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for("index"))

@app.route('/genreport', methods=['POST','GET'])
def genreport():
    #report_data = Btqueue.query.filter_by(service_status=1).all()
    report_data = Btqueue.query.all()
    return render_template('genreport.html', report_data=report_data)

@app.route('/range', methods=['POST', 'GET'])
def range():
    if request.method == 'POST':
        report_from = request.form.get('From')
        report_to = request.form.get('to')
        Patient_procedure = request.form.get('Patient_procedure')

        try:
            # Parse dates
            report_from = datetime.strptime(report_from, '%Y-%m-%d')
            report_to = datetime.strptime(report_to, '%Y-%m-%d')

            # Query database
            '''
            if Patient_procedure != "1":
                query_report = Btqueue.query.filter(
                    Btqueue.arrival_time.between(report_from, report_to)
                ).all()
            else:
                query_report = Btqueue.query.filter(
                    Btqueue.pat_procedure == Patient_procedure,
                    Btqueue.arrival_time.between(report_from, report_to)
                ).all()
            '''
            query_report = Btqueue.query.all()
            # Serialize results
            results = [
                {
                    "id": record.queue_id,
                    "pat_id": record.pat_id,
                    "pat_phone": record.pat_phone,
                    "pat_procedure": record.pat_procedure,
                    "arrival_time": record.arrival_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "departure_time": record.departure_time.strftime('%Y-%m-%d %H:%M:%S') if record.departure_time else None,
                    "service_status": record.service_status
                }
                for record in query_report
            ]
            return jsonify({'htmlresponse': render_template('response.html', ordersrange=results)})
            #return jsonify({'ordersrange': results})
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"status": "Error", "message": str(e)})
    return jsonify({"status": "Failure", "message": "Invalid request method"})


if __name__ =="__main__":
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', debug=True, port=5555)
