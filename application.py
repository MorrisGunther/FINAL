import os
import smtplib

# from email.MIMEMultipart import MIMEMultipart
# from email.MIMEText import MIMEText

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import manager_apology, employee_apology, login_required

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

    # If the request method is POST, do the below
    if request.method == "POST":

        # Apologises with the message "Missing name" if the new user (manager) did not provide his name
        if not request.form.get("full_name"):
            return manager_apology("Missing name")

        # Apologises with the message "Missing email address" if the new user (manager) did not provide a email address
        if not request.form.get("email"):
            return manager_apology("Missing email address")

        # Apologises with the message "Missing password" if the new user (manager) did not provide a password in the first password field
        if not request.form.get("password"):
            return manager_apology("Missing password")

        # Apologises with the message "Passwords don't match" if the new user (manager) did not provide a password in the confirmation field or the passwords in
        # The password field and in the confirmation field do not match
        if not request.form.get("confirmation") or request.form.get("password") != request.form.get("confirmation"):
            return manager_apology("Passwords don't match")

        # Hashes the password provided by the user (manager)
        hashed_password = generate_password_hash(request.form.get("password"))

        # Inserts the new user (manager) (i.e. full name, email address, hashed password, type of user) to the table "user" of the database
        # (the below function will return "none" if the provided email address already exists in the table "users", since the field
        # "email_address" is a unique field in the table)
        result = db.execute("INSERT INTO users (manager_name, email_address, hash, manager_or_employee) \
                            VALUES (:manager_name, :email_address, :hashed_password, 'manager')",
                            manager_name=request.form.get("full_name"), email_address=request.form.get("email"),
                            hashed_password=hashed_password)

        # Apologises with the message "Email is not available" if the provided email address already exists in the table "users"
        if not result:
            return manager_apology("Email is not available")

        # Logs the new user (manager) in by storing his/her id number in sessions
        id_ = db.execute("SELECT id FROM users WHERE email_address = :email_address", email_address=request.form.get("email"))
        session["user_id"] = id_[0]["id"]

        # Redirects the new user (manager) to the homepage for managers
        return redirect("/")

    # If the request method is GET, this renders the template "register.html" via which a person can register for the site
    else:
        return render_template("register.html")


@app.route("/check_register", methods=["GET"])
def check_register():

    # Stores the email address that the user provided via /register in the variable "email_address"
    email_address = request.args.get("email")

    # If the user did not provide a email address or if there already is a user in the table "users" who has the same email address as the
    # One provided by the new user, this returns, in JSON format, false
    registered_users = db.execute("SELECT * FROM users WHERE email_address = :email_address", email_address=email_address)
    if not email_address or registered_users:
        return jsonify(False)

    # Otherwise, this returns, in JSON format, true
    return jsonify(True)

@app.route("/check_requests", methods=["GET"])
@login_required
def check_requests():

    # Stores the email address that the manager provided via /manager_request_feedback in the variable "email_address"
    email_address = request.args.get("email")

    registered_users = db.execute("SELECT * FROM users WHERE email_address = :email_address", email_address=email_address)

    if not email_address:
        return jsonify(1)

    elif registered_users:
        return jsonify(2)

    # Otherwise, this returns, in JSON format, true
    return jsonify(3)


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
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

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/")
@login_required
def manager_index():

# HTML ("manager_index.html") bearbeiten: Zwei Spalten: linke Spalte: Name des Feedbackgebers, rechte Spalte: Status (awaiting oder received)

    requested_employees = db.execute("SELECT id FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                     id_of_manager_to_be_assessed=session['user_id'])

    requested_employees_ = []

    for requested_employee in requested_employees:
        requested_employees_.append(requested_employee["id"])

    employees_who_already_submitted_feedback = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                                          feedbackee_id=session['user_id'])

    employees_who_already_submitted_feedback_ = []

    for employee_who_already_submitted_feedback in employees_who_already_submitted_feedback:
        employees_who_already_submitted_feedback_.append(employee_who_already_submitted_feedback["feedbacker_id"])

    awaiting_or_received = []

    for requested_employee_ in requested_employees_:
        if requested_employee_ in employees_who_already_submitted_feedback_:
            awaiting_or_received.append("received")
        else:
            awaiting_or_received.append("awaiting")

    emails_of_requested_employees = db.execute("SELECT email_address FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                               id_of_manager_to_be_assessed=session['user_id'])

    emails_of_requested_employees_ = []

    for email_of_requested_employees in emails_of_requested_employees:
        emails_of_requested_employees_.append(email_of_requested_employees["email_address"])

    return render_template("manager_index.html",
                           awaiting_or_received=awaiting_or_received, emails_of_requested_employees_=emails_of_requested_employees_)


@app.route("/manager_request_feedback", methods=["GET", "POST"])
@login_required
def manager_request_feedback():

        #usign https://www.pythonforbeginners.com/code-snippets-source-code/using-python-to-send-email

        #message = "Here are your login credentials"
        #server = smtplib.SMTP('smtp.gmail.com', 587)
        #server.ehlo()
        #server.starttls()
        #server.login("annegegenmantel@gmail.com", os.getenv("password"))
        #server.sendmail("annegegenmantel@gmail.com", "annegegenmantel@gmail.com", message)

    if request.method == "POST":
        #feedback_givers = db.execute("SELECT email_address FROM users WHERE email_address =:email_address",
         #                            email_address=request.form.get("email"))
        #if not feedback_givers:
        result = db.execute("INSERT INTO users (email_address, hash, manager_or_employee, id_of_manager_to_be_assessed) \
                            VALUES (:email_address, 'hashed_passwordXXX', 'employee', :id_of_manager_to_be_assessed)",
                            email_address=request.form.get("email"), id_of_manager_to_be_assessed=session['user_id'])

        if not result:
            return manager_apology("A request has already been sent to this email address")

        return redirect("/manager_request_feedback")

    else:
        email_addresses = db.execute("SELECT email_address FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                     id_of_manager_to_be_assessed=session['user_id'])

        return render_template("manager_request_feedback.html", email_addresses=email_addresses)


@app.route("/manager_self_assessment", methods=["GET", "POST"])
@login_required
def manager_self_assessment():

    if request.method == "POST":
        Q1 = request.form.get("Q1")
        Q2 = request.form.get("Q2")
        Q3 = request.form.get("Q3")
        Q4 = request.form.get("Q4")
        Q5 = request.form.get("Q5")
        Q6 = request.form.get("Q6")
        Q7 = request.form.get("Q7")
        Q8 = request.form.get("Q8")
        Q9 = request.form.get("Q9")
        Q10 = request.form.get("Q10")
        Q11 = request.form.get("Q11")
        Q12 = request.form.get("Q12")
        Q13 = request.form.get("Q13")
        Q14 = request.form.get("Q14")
        Q15 = request.form.get("Q15")
        Q16 = request.form.get("Q16")
        Q17 = request.form.get("Q17")
        Q18 = request.form.get("Q18")
        Q19 = request.form.get("Q19")
        Q20 = request.form.get("Q20")
        Q21 = request.form.get("Q21")
        Q22 = request.form.get("Q22")
        Q23 = request.form.get("Q23")
        Q24 = request.form.get("Q24")
        Q25 = request.form.get("Q25")
        Q26 = request.form.get("Q26")
        Q27 = request.form.get("Q27")
        Q28 = request.form.get("Q28")
        Q29 = request.form.get("Q29")
        Q30 = request.form.get("Q30")
        Q31 = request.form.get("Q31")
        Q32 = request.form.get("Q32")
        Q33 = request.form.get("Q33")
        Q34 = request.form.get("Q34")
        Q35 = request.form.get("Q35")
        Q36 = request.form.get("Q36")
        Q37 = request.form.get("Q37")
        Q38 = request.form.get("Q38")
        Q39 = request.form.get("Q39")
        Q40 = request.form.get("Q40")

        # insert the survey values into the table
        db.execute("INSERT INTO surveyanswers(feedbacker_id, feedbackee_id, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, \
                   Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, Q33, Q34, Q35, Q36, \
                   Q37, Q38, Q39, Q40) VALUES (:feedbacker_id, :feedbackee_id, :Q1, :Q2, :Q3, :Q4, :Q5, :Q6, :Q7, :Q8, :Q9, :Q10, \
                   :Q11, :Q12, :Q13, :Q14, :Q15, :Q16, :Q17, :Q18, :Q19, :Q20, :Q21, :Q22, :Q23, :Q24, :Q25, :Q26, :Q27, \
                   :Q28, :Q29, :Q30, :Q31, :Q32, :Q33, :Q34, :Q35, :Q36, :Q37, :Q38, :Q39, :Q40)",
                   feedbacker_id=session['user_id'], feedbackee_id=session['user_id'], Q1=Q1, Q2=Q2, Q3=Q3, Q4=Q4, Q5=Q5, Q6=Q6, Q7=Q7, Q8=Q8,
                   Q9=Q9, Q10=Q10, Q11=Q11, Q12=Q12, Q13=Q13, Q14=Q14, Q15=Q15, Q16=Q16, Q17=Q17, Q18=Q18, Q19=Q19, Q20=Q20, Q21=Q21, Q22=Q22,
                   Q23=Q23, Q24=Q24, Q25=Q25, Q26=Q26, Q27=Q27, Q28=Q28, Q29=Q29, Q30=Q30, Q31=Q31, Q32=Q32, Q33=Q33, Q34=Q34, Q35=Q35,
                   Q36=Q36, Q37=Q37, Q38=Q38, Q39=Q39, Q40=Q40)

        return render_template("manager_self_assessment_success.html")

    else:
        feedbacker_ids = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                    feedbacker_id=session['user_id'])

        if not feedbacker_ids:
            return render_template("manager_self_assessment.html")
        else:
            return render_template("manager_self_assessment_already_submitted.html")


@app.route("/manager_view_report")
@login_required
def manager_view_report():

    # TODO
    return render_template("manager_view_report.html")


@app.route("/employee_index")
@login_required
def employee_index():
    return render_template("employee_index.html")


@app.route("/employee_provide_feedback", methods=["GET", "POST"])
@login_required
def employee_provide_feedback():

    if request.method == "POST":
        Q1 = request.form.get("Q1")
        Q2 = request.form.get("Q2")
        Q3 = request.form.get("Q3")
        Q4 = request.form.get("Q4")
        Q5 = request.form.get("Q5")
        Q6 = request.form.get("Q6")
        Q7 = request.form.get("Q7")
        Q8 = request.form.get("Q8")
        Q9 = request.form.get("Q9")
        Q10 = request.form.get("Q10")
        Q11 = request.form.get("Q11")
        Q12 = request.form.get("Q12")
        Q13 = request.form.get("Q13")
        Q14 = request.form.get("Q14")
        Q15 = request.form.get("Q15")
        Q16 = request.form.get("Q16")
        Q17 = request.form.get("Q17")
        Q18 = request.form.get("Q18")
        Q19 = request.form.get("Q19")
        Q20 = request.form.get("Q20")
        Q21 = request.form.get("Q21")
        Q22 = request.form.get("Q22")
        Q23 = request.form.get("Q23")
        Q24 = request.form.get("Q24")
        Q25 = request.form.get("Q25")
        Q26 = request.form.get("Q26")
        Q27 = request.form.get("Q27")
        Q28 = request.form.get("Q28")
        Q29 = request.form.get("Q29")
        Q30 = request.form.get("Q30")
        Q31 = request.form.get("Q31")
        Q32 = request.form.get("Q32")
        Q33 = request.form.get("Q33")
        Q34 = request.form.get("Q34")
        Q35 = request.form.get("Q35")
        Q36 = request.form.get("Q36")
        Q37 = request.form.get("Q37")
        Q38 = request.form.get("Q38")
        Q39 = request.form.get("Q39")
        Q40 = request.form.get("Q40")

        feedbackee_id = db.execute("SELECT id_of_manager_to_be_assessed FROM users WHERE id=:id_", id_=session['user_id'])
        feedbackee_id_ = feedbackee_id[0]["id_of_manager_to_be_assessed"]

        # insert the survey values into the table
        db.execute("INSERT INTO surveyanswers(feedbacker_id, feedbackee_id, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, \
                   Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, \
                   Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40) VALUES (:feedbacker_id, :feedbackee_id, :Q1, :Q2, :Q3, :Q4, :Q5, \
                   :Q6, :Q7, :Q8, :Q9, :Q10, :Q11, :Q12, :Q13, :Q14, :Q15, :Q16, :Q17, :Q18, :Q19, :Q20, :Q21, :Q22, :Q23, \
                   :Q24, :Q25, :Q26, :Q27, :Q28, :Q29, :Q30, :Q31, :Q32, :Q33, :Q34, :Q35, :Q36, :Q37, :Q38, :Q39, :Q40)",
                   feedbacker_id=session['user_id'], feedbackee_id=feedbackee_id_, Q1=Q1, Q2=Q2, Q3=Q3, Q4=Q4, Q5=Q5, Q6=Q6, Q7=Q7, Q8=Q8, Q9=Q9, Q10=Q10, Q11=Q11,
                   Q12=Q12, Q13=Q13, Q14=Q14, Q15=Q15, Q16=Q16, Q17=Q17, Q18=Q18, Q19=Q19, Q20=Q20, Q21=Q21, Q22=Q22, Q23=Q23,
                   Q24=Q24, Q25=Q25, Q26=Q26, Q27=Q27, Q28=Q28, Q29=Q29, Q30=Q30, Q31=Q31, Q32=Q32, Q33=Q33, Q34=Q34, Q35=Q35,
                   Q36=Q36, Q37=Q37, Q38=Q38, Q39=Q39, Q40=Q40)

        return render_template("employee_provide_feedback_success.html")

    else:
        feedbacker_ids = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                    feedbacker_id=session['user_id'])

        if not feedbacker_ids:
            id_of_manager_to_be_assessed = db.execute("SELECT id_of_manager_to_be_assessed FROM users WHERE id=:id_", id_=session['user_id'])
            id_of_manager_to_be_assessed_ = id_of_manager_to_be_assessed[0]["id_of_manager_to_be_assessed"]
            manager_name = db.execute("SELECT manager_name FROM users WHERE id=:id_of_manager_to_be_assessed_",
                                      id_of_manager_to_be_assessed_=id_of_manager_to_be_assessed_)
            manager_name_ = manager_name[0]["manager_name"]

            return render_template("employee_provide_feedback.html", manager_name_=manager_name_)

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
import os
import smtplib

# from email.MIMEMultipart import MIMEMultipart
# from email.MIMEText import MIMEText

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import manager_apology, employee_apology, login_required

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

    # If the request method is POST, do the below
    if request.method == "POST":

        # Apologises with the message "Missing name" if the new user (manager) did not provide his name
        if not request.form.get("full_name"):
            return manager_apology("Missing name")

        # Apologises with the message "Missing email address" if the new user (manager) did not provide a email address
        if not request.form.get("email"):
            return manager_apology("Missing email address")

        # Apologises with the message "Missing password" if the new user (manager) did not provide a password in the first password field
        if not request.form.get("password"):
            return manager_apology("Missing password")

        # Apologises with the message "Passwords don't match" if the new user (manager) did not provide a password in the confirmation field or the passwords in
        # The password field and in the confirmation field do not match
        if not request.form.get("confirmation") or request.form.get("password") != request.form.get("confirmation"):
            return manager_apology("Passwords don't match")

        # Hashes the password provided by the user (manager)
        hashed_password = generate_password_hash(request.form.get("password"))

        # Inserts the new user (manager) (i.e. full name, email address, hashed password, type of user) to the table "user" of the database
        # (the below function will return "none" if the provided email address already exists in the table "users", since the field
        # "email_address" is a unique field in the table)
        result = db.execute("INSERT INTO users (manager_name, email_address, hash, manager_or_employee) \
                            VALUES (:manager_name, :email_address, :hashed_password, 'manager')",
                            manager_name=request.form.get("full_name"), email_address=request.form.get("email"),
                            hashed_password=hashed_password)

        # Apologises with the message "Email is not available" if the provided email address already exists in the table "users"
        if not result:
            return manager_apology("Email is not available")

        # Logs the new user (manager) in by storing his/her id number in sessions
        id_ = db.execute("SELECT id FROM users WHERE email_address = :email_address", email_address=request.form.get("email"))
        session["user_id"] = id_[0]["id"]

        # Redirects the new user (manager) to the homepage for managers
        return redirect("/")

    # If the request method is GET, this renders the template "register.html" via which a person can register for the site
    else:
        return render_template("register.html")


@app.route("/check_register", methods=["GET"])
def check_register():

    # Stores the email address that the user provided via /register in the variable "email_address"
    email_address = request.args.get("email")

    # If the user did not provide a email address or if there already is a user in the table "users" who has the same email address as the
    # One provided by the new user, this returns, in JSON format, false
    registered_users = db.execute("SELECT * FROM users WHERE email_address = :email_address", email_address=email_address)
    if not email_address or registered_users:
        return jsonify(False)

    # Otherwise, this returns, in JSON format, true
    return jsonify(True)

@app.route("/check_requests", methods=["GET"])
@login_required
def check_requests():

    # Stores the email address that the manager provided via /manager_request_feedback in the variable "email_address"
    email_address = request.args.get("email")

    registered_users = db.execute("SELECT * FROM users WHERE email_address = :email_address", email_address=email_address)

    if not email_address:
        return jsonify(1)

    elif registered_users:
        return jsonify(2)

    # Otherwise, this returns, in JSON format, true
    return jsonify(3)


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
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

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/")
@login_required
def manager_index():

# HTML ("manager_index.html") bearbeiten: Zwei Spalten: linke Spalte: Name des Feedbackgebers, rechte Spalte: Status (awaiting oder received)

    requested_employees = db.execute("SELECT id FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                     id_of_manager_to_be_assessed=session['user_id'])

    requested_employees_ = []

    for requested_employee in requested_employees:
        requested_employees_.append(requested_employee["id"])

    employees_who_already_submitted_feedback = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                                          feedbackee_id=session['user_id'])

    employees_who_already_submitted_feedback_ = []

    for employee_who_already_submitted_feedback in employees_who_already_submitted_feedback:
        employees_who_already_submitted_feedback_.append(employee_who_already_submitted_feedback["feedbacker_id"])

    awaiting_or_received = []

    for requested_employee_ in requested_employees_:
        if requested_employee_ in employees_who_already_submitted_feedback_:
            awaiting_or_received.append("received")
        else:
            awaiting_or_received.append("awaiting")

    emails_of_requested_employees = db.execute("SELECT email_address FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                               id_of_manager_to_be_assessed=session['user_id'])

    emails_of_requested_employees_ = []

    for email_of_requested_employees in emails_of_requested_employees:
        emails_of_requested_employees_.append(email_of_requested_employees["email_address"])

    return render_template("manager_index.html",
                           awaiting_or_received=awaiting_or_received, emails_of_requested_employees_=emails_of_requested_employees_)


@app.route("/manager_request_feedback", methods=["GET", "POST"])
@login_required
def manager_request_feedback():

        #usign https://www.pythonforbeginners.com/code-snippets-source-code/using-python-to-send-email

        #message = "Here are your login credentials"
        #server = smtplib.SMTP('smtp.gmail.com', 587)
        #server.ehlo()
        #server.starttls()
        #server.login("annegegenmantel@gmail.com", os.getenv("password"))
        #server.sendmail("annegegenmantel@gmail.com", "annegegenmantel@gmail.com", message)

    if request.method == "POST":
        #feedback_givers = db.execute("SELECT email_address FROM users WHERE email_address =:email_address",
         #                            email_address=request.form.get("email"))
        #if not feedback_givers:
        result = db.execute("INSERT INTO users (email_address, hash, manager_or_employee, id_of_manager_to_be_assessed) \
                            VALUES (:email_address, 'hashed_passwordXXX', 'employee', :id_of_manager_to_be_assessed)",
                            email_address=request.form.get("email"), id_of_manager_to_be_assessed=session['user_id'])

        if not result:
            return manager_apology("A request has already been sent to this email address")

        return redirect("/manager_request_feedback")

    else:
        email_addresses = db.execute("SELECT email_address FROM users WHERE id_of_manager_to_be_assessed=:id_of_manager_to_be_assessed",
                                     id_of_manager_to_be_assessed=session['user_id'])

        return render_template("manager_request_feedback.html", email_addresses=email_addresses)


@app.route("/manager_self_assessment", methods=["GET", "POST"])
@login_required
def manager_self_assessment():

    if request.method == "POST":
        Q1 = request.form.get("Q1")
        Q2 = request.form.get("Q2")
        Q3 = request.form.get("Q3")
        Q4 = request.form.get("Q4")
        Q5 = request.form.get("Q5")
        Q6 = request.form.get("Q6")
        Q7 = request.form.get("Q7")
        Q8 = request.form.get("Q8")
        Q9 = request.form.get("Q9")
        Q10 = request.form.get("Q10")
        Q11 = request.form.get("Q11")
        Q12 = request.form.get("Q12")
        Q13 = request.form.get("Q13")
        Q14 = request.form.get("Q14")
        Q15 = request.form.get("Q15")
        Q16 = request.form.get("Q16")
        Q17 = request.form.get("Q17")
        Q18 = request.form.get("Q18")
        Q19 = request.form.get("Q19")
        Q20 = request.form.get("Q20")
        Q21 = request.form.get("Q21")
        Q22 = request.form.get("Q22")
        Q23 = request.form.get("Q23")
        Q24 = request.form.get("Q24")
        Q25 = request.form.get("Q25")
        Q26 = request.form.get("Q26")
        Q27 = request.form.get("Q27")
        Q28 = request.form.get("Q28")
        Q29 = request.form.get("Q29")
        Q30 = request.form.get("Q30")
        Q31 = request.form.get("Q31")
        Q32 = request.form.get("Q32")
        Q33 = request.form.get("Q33")
        Q34 = request.form.get("Q34")
        Q35 = request.form.get("Q35")
        Q36 = request.form.get("Q36")
        Q37 = request.form.get("Q37")
        Q38 = request.form.get("Q38")
        Q39 = request.form.get("Q39")
        Q40 = request.form.get("Q40")

        # insert the survey values into the table
        db.execute("INSERT INTO surveyanswers(feedbacker_id, feedbackee_id, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, \
                   Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, Q33, Q34, Q35, Q36, \
                   Q37, Q38, Q39, Q40) VALUES (:feedbacker_id, :feedbackee_id, :Q1, :Q2, :Q3, :Q4, :Q5, :Q6, :Q7, :Q8, :Q9, :Q10, \
                   :Q11, :Q12, :Q13, :Q14, :Q15, :Q16, :Q17, :Q18, :Q19, :Q20, :Q21, :Q22, :Q23, :Q24, :Q25, :Q26, :Q27, \
                   :Q28, :Q29, :Q30, :Q31, :Q32, :Q33, :Q34, :Q35, :Q36, :Q37, :Q38, :Q39, :Q40)",
                   feedbacker_id=session['user_id'], feedbackee_id=session['user_id'], Q1=Q1, Q2=Q2, Q3=Q3, Q4=Q4, Q5=Q5, Q6=Q6, Q7=Q7, Q8=Q8,
                   Q9=Q9, Q10=Q10, Q11=Q11, Q12=Q12, Q13=Q13, Q14=Q14, Q15=Q15, Q16=Q16, Q17=Q17, Q18=Q18, Q19=Q19, Q20=Q20, Q21=Q21, Q22=Q22,
                   Q23=Q23, Q24=Q24, Q25=Q25, Q26=Q26, Q27=Q27, Q28=Q28, Q29=Q29, Q30=Q30, Q31=Q31, Q32=Q32, Q33=Q33, Q34=Q34, Q35=Q35,
                   Q36=Q36, Q37=Q37, Q38=Q38, Q39=Q39, Q40=Q40)

        return render_template("manager_self_assessment_success.html")

    else:
        feedbacker_ids = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                    feedbacker_id=session['user_id'])

        if not feedbacker_ids:
            return render_template("manager_self_assessment.html")
        else:
            return render_template("manager_self_assessment_already_submitted.html")


@app.route("/manager_view_report")
@login_required
def manager_view_report():

    # TODO
    return render_template("manager_view_report.html")


@app.route("/employee_index")
@login_required
def employee_index():
    return render_template("employee_index.html")


@app.route("/employee_provide_feedback", methods=["GET", "POST"])
@login_required
def employee_provide_feedback():

    if request.method == "POST":
        Q1 = request.form.get("Q1")
        Q2 = request.form.get("Q2")
        Q3 = request.form.get("Q3")
        Q4 = request.form.get("Q4")
        Q5 = request.form.get("Q5")
        Q6 = request.form.get("Q6")
        Q7 = request.form.get("Q7")
        Q8 = request.form.get("Q8")
        Q9 = request.form.get("Q9")
        Q10 = request.form.get("Q10")
        Q11 = request.form.get("Q11")
        Q12 = request.form.get("Q12")
        Q13 = request.form.get("Q13")
        Q14 = request.form.get("Q14")
        Q15 = request.form.get("Q15")
        Q16 = request.form.get("Q16")
        Q17 = request.form.get("Q17")
        Q18 = request.form.get("Q18")
        Q19 = request.form.get("Q19")
        Q20 = request.form.get("Q20")
        Q21 = request.form.get("Q21")
        Q22 = request.form.get("Q22")
        Q23 = request.form.get("Q23")
        Q24 = request.form.get("Q24")
        Q25 = request.form.get("Q25")
        Q26 = request.form.get("Q26")
        Q27 = request.form.get("Q27")
        Q28 = request.form.get("Q28")
        Q29 = request.form.get("Q29")
        Q30 = request.form.get("Q30")
        Q31 = request.form.get("Q31")
        Q32 = request.form.get("Q32")
        Q33 = request.form.get("Q33")
        Q34 = request.form.get("Q34")
        Q35 = request.form.get("Q35")
        Q36 = request.form.get("Q36")
        Q37 = request.form.get("Q37")
        Q38 = request.form.get("Q38")
        Q39 = request.form.get("Q39")
        Q40 = request.form.get("Q40")

        feedbackee_id = db.execute("SELECT id_of_manager_to_be_assessed FROM users WHERE id=:id_", id_=session['user_id'])
        feedbackee_id_ = feedbackee_id[0]["id_of_manager_to_be_assessed"]

        # insert the survey values into the table
        db.execute("INSERT INTO surveyanswers(feedbacker_id, feedbackee_id, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, \
                   Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, \
                   Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40) VALUES (:feedbacker_id, :feedbackee_id, :Q1, :Q2, :Q3, :Q4, :Q5, \
                   :Q6, :Q7, :Q8, :Q9, :Q10, :Q11, :Q12, :Q13, :Q14, :Q15, :Q16, :Q17, :Q18, :Q19, :Q20, :Q21, :Q22, :Q23, \
                   :Q24, :Q25, :Q26, :Q27, :Q28, :Q29, :Q30, :Q31, :Q32, :Q33, :Q34, :Q35, :Q36, :Q37, :Q38, :Q39, :Q40)",
                   feedbacker_id=session['user_id'], feedbackee_id=feedbackee_id_, Q1=Q1, Q2=Q2, Q3=Q3, Q4=Q4, Q5=Q5, Q6=Q6, Q7=Q7, Q8=Q8, Q9=Q9, Q10=Q10, Q11=Q11,
                   Q12=Q12, Q13=Q13, Q14=Q14, Q15=Q15, Q16=Q16, Q17=Q17, Q18=Q18, Q19=Q19, Q20=Q20, Q21=Q21, Q22=Q22, Q23=Q23,
                   Q24=Q24, Q25=Q25, Q26=Q26, Q27=Q27, Q28=Q28, Q29=Q29, Q30=Q30, Q31=Q31, Q32=Q32, Q33=Q33, Q34=Q34, Q35=Q35,
                   Q36=Q36, Q37=Q37, Q38=Q38, Q39=Q39, Q40=Q40)

        return render_template("employee_provide_feedback_success.html")

    else:
        feedbacker_ids = db.execute("SELECT feedbacker_id FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                    feedbacker_id=session['user_id'])

        if not feedbacker_ids:
            id_of_manager_to_be_assessed = db.execute("SELECT id_of_manager_to_be_assessed FROM users WHERE id=:id_", id_=session['user_id'])
            id_of_manager_to_be_assessed_ = id_of_manager_to_be_assessed[0]["id_of_manager_to_be_assessed"]
            manager_name = db.execute("SELECT manager_name FROM users WHERE id=:id_of_manager_to_be_assessed_",
                                      id_of_manager_to_be_assessed_=id_of_manager_to_be_assessed_)
            manager_name_ = manager_name[0]["manager_name"]

            return render_template("employee_provide_feedback.html", manager_name_=manager_name_)

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
