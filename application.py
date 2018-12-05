import os
import smtplib

from random import choice
from string import ascii_uppercase, digits
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import manager_apology, employee_apology, login_required

import csv

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///leadership.db")


@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure name was submitted by the manager
        if not request.form.get("full_name"):
            return manager_apology("Missing name")

        # Ensure email address was submitted
        if not request.form.get("email"):
            return manager_apology("Missing email address")

        # Ensure password was submitted
        if not request.form.get("password"):
            return manager_apology("Missing password")

        # Ensure password was confirmed and passwords match
        if not request.form.get("confirmation") or request.form.get("password") != request.form.get("confirmation"):
            return manager_apology("Passwords don't match")

        # Hash the password provided by the user (manager)
        hashed_password = generate_password_hash(request.form.get("password"))

        # Insert the new user (manager) (i.e. full name, email address, hashed password, type of user) to the table "user" of the database
        result = db.execute("INSERT INTO users (manager_name, email_address, hash, manager_or_employee) \
                            VALUES (:manager_name, :email_address, :hashed_password, 'manager')",
                            manager_name=request.form.get("full_name"), email_address=request.form.get("email"),
                            hashed_password=hashed_password)

        # Apologise with the message "Email is not available" if the provided email address already exists in the table "users"
        if not result:
            return manager_apology("Email is not available")

        # Log the new user (manager) in by storing his/her id number in sessions
        id_ = db.execute("SELECT id FROM users WHERE email_address = :email_address", email_address=request.form.get("email"))
        session["user_id"] = id_[0]["id"]

        # Redirect the new user (manager) to the homepage for managers
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/check_register", methods=["GET"])
def check_register():

    # Store the email address that the user (manager) provided via /register in the variable "email_address"
    email_address = request.args.get("email")

    # If no email address provided or if there already is a user with the same email address, return, in JSON format, false
    registered_users = db.execute("SELECT * FROM users WHERE email_address = :email_address", email_address=email_address)
    if not email_address or registered_users:
        return jsonify(False)

    # Otherwise, return, in JSON format, true
    return jsonify(True)


@app.route("/check_requests", methods=["GET"])
@login_required
def check_requests():

    # Store the email address that the manager provided via /manager_request_feedback in the variable "email_address"
    email_address = request.args.get("email")

    registered_users = db.execute("SELECT * FROM users WHERE email_address = :email_address", email_address=email_address)

    # If no email_address provided, return, in JSON format, 1
    if not email_address:
        return jsonify(1)

    # If there already is a user with the same email address in the table "users", return, in JSON format, 2
    elif registered_users:
        return jsonify(2)

    # Otherwise, return, in JSON format, 3
    return jsonify(3)


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure email address was submitted
        if not request.form.get("email"):
            return manager_apology("must provide email address", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return manager_apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email_address = :email_address",
                          email_address=request.form.get("email"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return manager_apology("invalid email address and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # If user is manager, redirect user to the homepage for managers
        if rows[0]["manager_or_employee"] == "manager":
            return redirect("/")

        # If user is employee, redirect user to the homepage for employees
        if rows[0]["manager_or_employee"] == "employee":
            return redirect("/employee_index")

    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/manager_request_feedback", methods=["GET", "POST"])
@login_required
def manager_request_feedback():

    # User reached route via POST
    if request.method == "POST":

        # Create random password for the requested employee (for employee login) and store it in the variable "random_[...]_requested_employee"
        password_length = 12
        random_password_for_requested_employee = ''.join(choice(ascii_uppercase + digits) for i in range(password_length))

        # Hash the password and store it in the variable "hashed_password"
        hashed_password = generate_password_hash(random_password_for_requested_employee)

        # Insert the requested employee (i.e. email address, hashed password, type of user, id of his/her manager) in the table "users"
        result = db.execute("INSERT INTO users (email_address, hash, manager_or_employee, id_of_manager_to_be_assessed) \
                            VALUES (:email_address, :hashed_password, 'employee', :id_of_manager_to_be_assessed)",
                            email_address=request.form.get("email"), hashed_password=hashed_password,
                            id_of_manager_to_be_assessed=session['user_id'])

        # Ensure employee has not already been requested by the logged-in manager (or another manager)
        if not result:
            return manager_apology("A request has already been sent to this email address")

        # Store the content of the email (i.e. login credentials) which will be sent to the requested employee in the variables part1, part2
        # And part3
        a = "Dear Sir or Madam, \n\n this is a request to provide feedback for Mr/Mrs "
        b = db.execute("SELECT manager_name FROM users WHERE id=:id_", id_=session['user_id'])
        b_ = b[0]["manager_name"]
        c = ". Please click on the link below to start the process. \n\n Your login credentials are: \n Email address: "
        d = request.form.get("email")
        e = "\n Password: "
        f = random_password_for_requested_employee
        g = "\n\n"

        part1__ = [a, b_, c, d, e, f, g]
        part1_ = "".join(part1__)
        part1 = MIMEText(part1_, 'plain')
        part2 = MIMEText(u'<a href="http://ide50-morrisgunther.cs50.io:8080/">XXXwww.anmoleadership.com</a>','html')
        part3_ = "\n\n Sincerely, \n Your ANMO Team"
        part3 = MIMEText(part3_, 'plain')

        # Store the from address, to address, subject as well as gmail account and password of sender in corresponding variables
        sent_from = 'cs50.anmo@gmail.com'
        to = request.form.get("email")
        msg = MIMEMultipart('multipart')
        msg.attach(part1)
        msg.attach(part2)
        msg.attach(part3)
        msg['Subject'] = 'Feedback request for your manager'
        msg['From'] = sent_from
        msg['To'] = to
        gmail_user = 'cs50.anmo@gmail.com'
        gmail_password = 'HKUJZT45-A!fvgh'

        # Set up gmail server, login and send email to requested emplyoee
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, msg.as_string())

        # Redirect user (manager) to request feedback form
        return redirect("/manager_request_feedback")

    # User reached route via GET
    else:

        # Query database for the email addresses requested by the logged-in manager
        email_addresses = db.execute("SELECT email_address FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                     id_of_manager_to_be_assessed=session['user_id'])

        # Render request feedback form
        return render_template("manager_request_feedback.html", email_addresses=email_addresses)


@app.route("/")
@login_required
def manager_index():

    # Query database for name of logged-in manager
    manager_name = db.execute("SELECT manager_name FROM users WHERE id=:id_", id_=session['user_id'])
    manager_name = manager_name[0]["manager_name"]

    # Store the ids of employees requested by the logged-in manager in the list "requested_employees"
    requested_employees = db.execute("SELECT id FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                     id_of_manager_to_be_assessed=session['user_id'])
    requested_employees_ = []
    for requested_employee in requested_employees:
        requested_employees_.append(requested_employee["id"])

    # Store the ids of employees who have already submitted their feedback for the logged-in manager in the list "employees_[...]_feedback"
    employees_who_already_submitted_feedback = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                                          feedbackee_id=session['user_id'])
    employees_who_already_submitted_feedback_ = []
    for employee_who_already_submitted_feedback in employees_who_already_submitted_feedback:
        employees_who_already_submitted_feedback_.append(employee_who_already_submitted_feedback["feedbacker_id"])

    # Store the values "received" (for each requested employee who already submitted feedback) and "awaiting" in the list "awaiting_or_received"
    awaiting_or_received = []
    for requested_employee_ in requested_employees_:
        if requested_employee_ in employees_who_already_submitted_feedback_:
            awaiting_or_received.append("received")
        else:
            awaiting_or_received.append("awaiting")

    # Store the email addresses of employees who have already submitted their feedback for the logged-in manager in the list "emails_[...]yees_"
    emails_of_requested_employees = db.execute("SELECT email_address FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                               id_of_manager_to_be_assessed=session['user_id'])
    emails_of_requested_employees_ = []
    for email_of_requested_employees in emails_of_requested_employees:
        emails_of_requested_employees_.append(email_of_requested_employees["email_address"])

    # Render manager index form
    return render_template("manager_index.html", manager_name=manager_name, awaiting_or_received=awaiting_or_received,
                           emails_of_requested_employees_=emails_of_requested_employees_)


@app.route("/manager_self_assessment", methods=["GET", "POST"])
@login_required
def manager_self_assessment():

    # User reached route via POST
    if request.method == "POST":

        # Ensure all questions have been answered
        for i in range(40):
            j = i + 1
            k = "Q" + str(j)
            if not request.form.get(k):
                return manager_apology("Please answer all questions!")

        # Insert the values of the self-assessment form into the table "surveyanswers"
        db.execute("INSERT INTO surveyanswers(feedbacker_id, feedbackee_id, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, \
                   Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, Q33, Q34, Q35, Q36, \
                   Q37, Q38, Q39, Q40) VALUES (:feedbacker_id, :feedbackee_id, :Q1, :Q2, :Q3, :Q4, :Q5, :Q6, :Q7, :Q8, :Q9, :Q10, \
                   :Q11, :Q12, :Q13, :Q14, :Q15, :Q16, :Q17, :Q18, :Q19, :Q20, :Q21, :Q22, :Q23, :Q24, :Q25, :Q26, :Q27, \
                   :Q28, :Q29, :Q30, :Q31, :Q32, :Q33, :Q34, :Q35, :Q36, :Q37, :Q38, :Q39, :Q40)",
                   feedbacker_id=session['user_id'], feedbackee_id=session['user_id'], Q1=request.form.get("Q1"), Q2=request.form.get("Q2"),
                   Q3=request.form.get("Q3"), Q4=request.form.get("Q4"), Q5=request.form.get("Q5"), Q6=request.form.get("Q6"),
                   Q7=request.form.get("Q7"), Q8=request.form.get("Q8"), Q9=request.form.get("Q9"), Q10=request.form.get("Q10"),
                   Q11=request.form.get("Q11"), Q12=request.form.get("Q12"), Q13=request.form.get("Q13"), Q14=request.form.get("Q14"),
                   Q15=request.form.get("Q15"), Q16=request.form.get("Q16"), Q17=request.form.get("Q17"), Q18=request.form.get("Q18"),
                   Q19=request.form.get("Q19"), Q20=request.form.get("Q20"), Q21=request.form.get("Q21"), Q22=request.form.get("Q22"),
                   Q23=request.form.get("Q23"), Q24=request.form.get("Q24"), Q25=request.form.get("Q25"), Q26=request.form.get("Q26"),
                   Q27=request.form.get("Q27"), Q28=request.form.get("Q28"), Q29=request.form.get("Q29"), Q30=request.form.get("Q30"),
                   Q31=request.form.get("Q31"), Q32=request.form.get("Q32"), Q33=request.form.get("Q33"), Q34=request.form.get("Q34"),
                   Q35=request.form.get("Q35"), Q36=request.form.get("Q36"), Q37=request.form.get("Q37"), Q38=request.form.get("Q38"),
                   Q39=request.form.get("Q39"), Q40=request.form.get("Q40"))

        # Render manager self-assessment form
        return render_template("manager_self_assessment_success.html")

    # User reached route via GET
    else:

        # Query database whether the manager has already submitted his/her self-assessment
        feedbacker_ids = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                    feedbacker_id=session['user_id'])

        # If manager has not assessed himself so far, render self-assessment form
        if not feedbacker_ids:
            return render_template("manager_self_assessment.html")

        # If manager has already assessed himself, render self assessment already submitted form
        else:
            return render_template("manager_self_assessment_already_submitted.html")


@app.route("/manager_view_report")
@login_required
def manager_view_report():

    self_assessment = db.execute("SELECT * FROM surveyanswers WHERE feedbacker_id= :feedbacker_id", feedbacker_id=session['user_id'])

    employee_feedback = db.execute("SELECT * FROM surveyanswers WHERE feedbackee_id= :feedbackee_id AND feedbacker_id!= :feedbacker_id",
                                   feedbackee_id=session['user_id'], feedbacker_id=session['user_id'])

    if not self_assessment or not employee_feedback:
        return render_template("manager_report_not_available.html")



    # TODOS: Overall score employees, self, assessment, Anzahl Feedbackgeber, Durchschnittsscore für jede einzelne Frage
    # aus employee feedback

    manager_name = db.execute("SELECT manager_name FROM users WHERE id=:id_", id_=session['user_id'])
    manager_name_ = manager_name[0]["manager_name"]

    employee_feedback_results = db.execute("SELECT AVG(Q1), AVG(Q2), AVG(Q3), AVG(Q4), AVG(Q5), AVG(Q6), AVG(Q7), AVG(Q8), AVG(Q9), AVG(Q10), \
                                           AVG(Q11), AVG(Q12), AVG(Q13), AVG(Q14), AVG(Q15), AVG(Q16), AVG(Q17), AVG(Q18), AVG(Q19), AVG(Q20), \
                                           AVG(Q21), AVG(Q22), AVG(Q23), AVG(Q24), AVG(Q25), AVG(Q26), AVG(Q27), AVG(Q28), AVG(Q29), AVG(Q30), \
                                           AVG(Q31), AVG(Q32), AVG(Q33), AVG(Q34), AVG(Q35), AVG(Q36), AVG(Q37), AVG(Q38), AVG(Q39), AVG(Q40) \
                                           FROM surveyanswers WHERE feedbackee_id= :feedbackee_id AND feedbacker_id!= :feedbacker_id",
                                           feedbackee_id=session['user_id'], feedbacker_id=session['user_id'])

    self_assessment_results = db.execute("SELECT AVG(Q1), AVG(Q2), AVG(Q3), AVG(Q4), AVG(Q5), AVG(Q6), AVG(Q7), AVG(Q8), AVG(Q9), AVG(Q10), \
                                         AVG(Q11), AVG(Q12), AVG(Q13), AVG(Q14), AVG(Q15), AVG(Q16), AVG(Q17), AVG(Q18), AVG(Q19), AVG(Q20), \
                                         AVG(Q21), AVG(Q22), AVG(Q23), AVG(Q24), AVG(Q25), AVG(Q26), AVG(Q27), AVG(Q28), AVG(Q29), AVG(Q30), \
                                         AVG(Q31), AVG(Q32), AVG(Q33), AVG(Q34), AVG(Q35), AVG(Q36), AVG(Q37), AVG(Q38), AVG(Q39), AVG(Q40) \
                                         FROM surveyanswers WHERE feedbacker_id= :feedbacker_id", feedbacker_id=session['user_id'])

    number_of_feedbackers = len(employee_feedback_results)




    employee_feedback_results_dict = employee_feedback_results[0]
    self_assessment_results_dict = self_assessment_results[0]

    WritetoCsv(employee_feedback_results_dict, 'static/data/employee_feedback.csv')
    WritetoCsv(self_assessment_results_dict, 'static/data/self_assessment.csv')

    return render_template("manager_view_report.html")

def WritetoCsv(dictionary, name_of_csvfile):
    category_lengths = [7, 10, 7, 7, 7, 2]
    results = []
    lower_boundary = 1
    upper_boundary = category_lengths[0] + 1
    # iterate over categories
    for i in range(len(category_lengths)):
        total = 0
        # iterate over questions
        for j in range (lower_boundary, upper_boundary):
            s = "AVG(Q" + str(j) + ")"
            total += dictionary[s]
        category_average = round(total/int(category_lengths[i]), 2)
        results.append(category_average)
        if i < 5:
            lower_boundary = upper_boundary
            upper_boundary += int(category_lengths[i+1])

    results_ = []
    for i in range(len(category_lengths)):
        results_.append({"categoryID": i + 1, "score": results[i]})

    csv_columns = ['categoryID','score']
    with open(name_of_csvfile, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for result in results_:
            writer.writerow(result)


@app.route("/employee_index")
@login_required
def employee_index():

    # Render employee index form
    return render_template("employee_index.html")


@app.route("/employee_provide_feedback", methods=["GET", "POST"])
@login_required
def employee_provide_feedback():

    # User reached route via POST
    if request.method == "POST":

        # Ensure all questions have been answered
        for i in range(40):
            j = i + 1
            k = "Q" + str(j)
            if not request.form.get(k):
                return manager_apology("Please answer all questions!")

        # Store the id of the manager to be assessed in the variable "feedbackee_id_"
        feedbackee_id = db.execute("SELECT id_of_manager_to_be_assessed FROM users WHERE id=:id_", id_=session['user_id'])
        feedbackee_id_ = feedbackee_id[0]["id_of_manager_to_be_assessed"]

        # Insert the values of the feedback form into the table "surveyanswers"
        db.execute("INSERT INTO surveyanswers(feedbacker_id, feedbackee_id, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, \
                   Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, \
                   Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40) VALUES (:feedbacker_id, :feedbackee_id, :Q1, :Q2, :Q3, :Q4, :Q5, \
                   :Q6, :Q7, :Q8, :Q9, :Q10, :Q11, :Q12, :Q13, :Q14, :Q15, :Q16, :Q17, :Q18, :Q19, :Q20, :Q21, :Q22, :Q23, \
                   :Q24, :Q25, :Q26, :Q27, :Q28, :Q29, :Q30, :Q31, :Q32, :Q33, :Q34, :Q35, :Q36, :Q37, :Q38, :Q39, :Q40)",
                   feedbacker_id=session['user_id'], feedbackee_id=feedbackee_id_, Q1=request.form.get("Q1"), Q2=request.form.get("Q2"),
                   Q3=request.form.get("Q3"), Q4=request.form.get("Q4"), Q5=request.form.get("Q5"), Q6=request.form.get("Q6"),
                   Q7=request.form.get("Q7"), Q8=request.form.get("Q8"), Q9=request.form.get("Q9"), Q10=request.form.get("Q10"),
                   Q11=request.form.get("Q11"), Q12=request.form.get("Q12"), Q13=request.form.get("Q13"), Q14=request.form.get("Q14"),
                   Q15=request.form.get("Q15"), Q16=request.form.get("Q16"), Q17=request.form.get("Q17"), Q18=request.form.get("Q18"),
                   Q19=request.form.get("Q19"), Q20=request.form.get("Q20"), Q21=request.form.get("Q21"), Q22=request.form.get("Q22"),
                   Q23=request.form.get("Q23"), Q24=request.form.get("Q24"), Q25=request.form.get("Q25"), Q26=request.form.get("Q26"),
                   Q27=request.form.get("Q27"), Q28=request.form.get("Q28"), Q29=request.form.get("Q29"), Q30=request.form.get("Q30"),
                   Q31=request.form.get("Q31"), Q32=request.form.get("Q32"), Q33=request.form.get("Q33"), Q34=request.form.get("Q34"),
                   Q35=request.form.get("Q35"), Q36=request.form.get("Q36"), Q37=request.form.get("Q37"), Q38=request.form.get("Q38"),
                   Q39=request.form.get("Q39"), Q40=request.form.get("Q40"))

        # Render employee provide feedback success form
        return render_template("employee_provide_feedback_success.html")

    # User reached route via GET
    else:

        # Query database whether the logged-in user has already submitted feedback
        feedbacker_id_ = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                    feedbacker_id=session['user_id'])

        # If the logged-in employee did not provide feedback so far, do the below:
        if not feedbacker_id_:

            # Query the database for the name of the manager to be assessed and store it in the variable "manager_name_"
            id_of_manager_to_be_assessed = db.execute("SELECT id_of_manager_to_be_assessed FROM users WHERE id=:id_", id_=session['user_id'])
            id_of_manager_to_be_assessed_ = id_of_manager_to_be_assessed[0]["id_of_manager_to_be_assessed"]
            manager_name = db.execute("SELECT manager_name FROM users WHERE id=:id_of_manager_to_be_assessed_",
                                      id_of_manager_to_be_assessed_=id_of_manager_to_be_assessed_)
            manager_name_ = manager_name[0]["manager_name"]

            # Render employee provide feedback form
            return render_template("employee_provide_feedback.html", manager_name_=manager_name_)

        # If the logged-in employee has already provided feedback, render employee feedback already submitted form
        else:
            return render_template("employee_feedback_already_submitted.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return manager_apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
