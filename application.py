import os
import smtplib

from random import choice
from string import ascii_uppercase, digits
from email.mime.text import MIMEText
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

    manager_name = db.execute("SELECT manager_name FROM users WHERE id=:id_", id_=session['user_id'])
    manager_name = manager_name[0]["manager_name"]

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

    return render_template("manager_index.html", manager_name=manager_name, awaiting_or_received=awaiting_or_received,
                           emails_of_requested_employees_=emails_of_requested_employees_)


@app.route("/manager_request_feedback", methods=["GET", "POST"])
@login_required
def manager_request_feedback():

    if request.method == "POST":
        password_length = 12
        random_password_for_requested_employee = ''.join(choice(ascii_uppercase + digits) for i in range(password_length))
        hashed_password = generate_password_hash(random_password_for_requested_employee)

        result = db.execute("INSERT INTO users (email_address, hash, manager_or_employee, id_of_manager_to_be_assessed) \
                            VALUES (:email_address, :hashed_password, 'employee', :id_of_manager_to_be_assessed)",
                            email_address=request.form.get("email"), hashed_password=hashed_password,
                            id_of_manager_to_be_assessed=session['user_id'])

        if not result:
            return manager_apology("A request has already been sent to this email address")

        a = "Dear Sir or Madam, \n\n this is a request to provide feedback for Mr/Mrs "
        b = db.execute("SELECT manager_name FROM users WHERE id=:id_", id_=session['user_id'])
        b_ = b[0]["manager_name"]
        c = ". Please click on the link below to start the process. \n\n Your login credentials are: \n Email address: "
        d = request.form.get("email")
        e = "\n Password: "
        f = random_password_for_requested_employee
        g = "\n\n"
        #TODO#h = u'<a href="www.google.com">abc</a>','html'
        h = "XXXlink"
        i = "\n\n Sincerely, \n Your ANMO Team"
        message_ = [a, b_, c, d, e, f, g, h, i]
        message = "".join(message_)
        sent_from = 'cs50.anmo@gmail.com'
        to  = request.form.get("email")
        msg = MIMEText(message)
        msg['Subject'] = 'Feedback request for your manager'
        msg['From'] = sent_from
        msg['To'] = to

        gmail_user = 'cs50.anmo@gmail.com'
        gmail_password = 'HKUJZT45-A!fvgh'
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, msg.as_string())

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

    manager_name = db.execute("SELECT manager_name FROM users WHERE id=:id_", id_=session['user_id'])
    manager_name = manager_name[0]["manager_name"]


    mtasksresult = db.execute("SELECT Q1, Q2, Q3, Q4, Q5, Q6, Q7 FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                         feedbacker_id=session['user_id'])
    mmanagerresult = db.execute("SELECT Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17 FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                         feedbacker_id=session['user_id'])
    mvisionresult = db.execute("SELECT Q18, Q19, Q20, Q21, Q22, Q23, Q24 FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                         feedbacker_id=session['user_id'])
    mteamresult = db.execute("SELECT Q25, Q26, Q27, Q28, Q29, Q30, Q31 FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                         feedbacker_id=session['user_id'])
    minnovationresult = db.execute("SELECT Q32, Q33, Q34, Q35, Q36, Q37, Q38 FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                         feedbacker_id=session['user_id'])
    mhappinnessresult = db.execute("SELECT Q39, Q40 FROM surveyanswers WHERE feedbacker_id=:feedbacker_id",
                                         feedbacker_id=session['user_id'])

    print(mhappinnessresult)

    etasksresult = db.execute("SELECT AVG(Q1), AVG(Q2), AVG(Q3), AVG(Q4), AVG(Q5), AVG(Q6), AVG(Q7) FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                         feedbackee_id=session['user_id'])
    emanagerresult = db.execute("SELECT AVG(Q8), AVG(Q9), AVG(Q10), AVG(Q11), AVG(Q12), AVG(Q13), AVG(Q14), AVG(Q15), AVG(Q16), AVG(Q17) FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                         feedbackee_id=session['user_id'])
    evisionresult = db.execute("SELECT AVG(Q18), AVG(Q19), AVG(Q20), AVG(Q21), AVG(Q22), AVG(Q23), AVG(Q24) FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                         feedbackee_id=session['user_id'])
    eteamresult = db.execute("SELECT AVG(Q25), AVG(Q26), AVG(Q27), AVG(Q28), AVG(Q29), AVG(Q30), AVG(Q31) FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                         feedbackee_id=session['user_id'])
    einnovationresult = db.execute("SELECT AVG(Q32), AVG(Q33), AVG(Q34), AVG(Q35), AVG(Q36), AVG(Q37), AVG(Q38) FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                         feedbackee_id=session['user_id'])
    ehappinnessresult = db.execute("SELECT AVG(Q39), AVG(Q40) FROM surveyanswers WHERE feedbackee_id=:feedbackee_id",
                                         feedbackee_id=session['user_id'])
    print(ehappinnessresult)

    mtasksresult_ = []
    for onemtasksresult in mtasksresult:
        mtasksresult_.append(onemtasksresult["Q1"])
        mtasksresult_.append(onemtasksresult["Q2"])
        mtasksresult_.append(onemtasksresult["Q3"])
        mtasksresult_.append(onemtasksresult["Q4"])
        mtasksresult_.append(onemtasksresult["Q5"])
        mtasksresult_.append(onemtasksresult["Q6"])
        mtasksresult_.append(onemtasksresult["Q7"])
    print(mtasksresult_)

    mmanagerresult_ = []
    for onemmanagerresult in mmanagerresult:
        mmanagerresult_.append(onemmanagerresult["Q8"])
        mmanagerresult_.append(onemmanagerresult["Q9"])
        mmanagerresult_.append(onemmanagerresult["Q10"])
        mmanagerresult_.append(onemmanagerresult["Q11"])
        mmanagerresult_.append(onemmanagerresult["Q12"])
        mmanagerresult_.append(onemmanagerresult["Q13"])
        mmanagerresult_.append(onemmanagerresult["Q14"])
        mmanagerresult_.append(onemmanagerresult["Q15"])
        mmanagerresult_.append(onemmanagerresult["Q16"])
        mmanagerresult_.append(onemmanagerresult["Q17"])
    print(mmanagerresult_)

    mvisionresult_ = []
    for onemvisionresult in mvisionresult:
        mvisionresult_.append(onemvisionresult["Q18"])
        mvisionresult_.append(onemvisionresult["Q19"])
        mvisionresult_.append(onemvisionresult["Q20"])
        mvisionresult_.append(onemvisionresult["Q21"])
        mvisionresult_.append(onemvisionresult["Q22"])
        mvisionresult_.append(onemvisionresult["Q23"])
        mvisionresult_.append(onemvisionresult["Q24"])
    print(mvisionresult_)

    mteamresult_ = []
    for onemteamresult in mteamresult:
        mteamresult_.append(onemteamresult["Q25"])
        mteamresult_.append(onemteamresult["Q26"])
        mteamresult_.append(onemteamresult["Q27"])
        mteamresult_.append(onemteamresult["Q28"])
        mteamresult_.append(onemteamresult["Q29"])
        mteamresult_.append(onemteamresult["Q30"])
        mteamresult_.append(onemteamresult["Q31"])
    print(mteamresult_)

    minnovationresult_ = []
    for oneminnovationresult in minnovationresult:
        minnovationresult_.append(oneminnovationresult["Q32"])
        minnovationresult_.append(oneminnovationresult["Q33"])
        minnovationresult_.append(oneminnovationresult["Q34"])
        minnovationresult_.append(oneminnovationresult["Q35"])
        minnovationresult_.append(oneminnovationresult["Q36"])
        minnovationresult_.append(oneminnovationresult["Q37"])
        minnovationresult_.append(oneminnovationresult["Q38"])
    print(minnovationresult_)

    mhappinnessresult_ = []
    for onemhappinnessresult in mhappinnessresult:
        mhappinnessresult_.append(onemhappinnessresult["Q39"])
        mhappinnessresult_.append(onemhappinnessresult["Q40"])
    print(mhappinnessresult_)

    etasksresult_ = []
    for oneetasksresult in etasksresult:
        etasksresult_.append(oneetasksresult["AVG(Q1)"])
        etasksresult_.append(oneetasksresult["AVG(Q2)"])
        etasksresult_.append(oneetasksresult["AVG(Q3)"])
        etasksresult_.append(oneetasksresult["AVG(Q4)"])
        etasksresult_.append(oneetasksresult["AVG(Q5)"])
        etasksresult_.append(oneetasksresult["AVG(Q6)"])
        etasksresult_.append(oneetasksresult["AVG(Q7)"])
    print(etasksresult_)

    emanagerresult_ = []
    for oneemanagerresult in emanagerresult:
        emanagerresult_.append(oneemanagerresult["AVG(Q8)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q9)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q10)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q11)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q12)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q13)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q14)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q15)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q16)"])
        emanagerresult_.append(oneemanagerresult["AVG(Q17)"])
    print(emanagerresult_)

    evisionresult_ = []
    for oneevisionresult in evisionresult:
        evisionresult_.append(oneevisionresult["AVG(Q18)"])
        evisionresult_.append(oneevisionresult["AVG(Q19)"])
        evisionresult_.append(oneevisionresult["AVG(Q20)"])
        evisionresult_.append(oneevisionresult["AVG(Q21)"])
        evisionresult_.append(oneevisionresult["AVG(Q22)"])
        evisionresult_.append(oneevisionresult["AVG(Q23)"])
        evisionresult_.append(oneevisionresult["AVG(Q24)"])
    print(evisionresult_)

    eteamresult_ = []
    for oneeteamresult in eteamresult:
        eteamresult_.append(oneeteamresult["AVG(Q25)"])
        eteamresult_.append(oneeteamresult["AVG(Q26)"])
        eteamresult_.append(oneeteamresult["AVG(Q27)"])
        eteamresult_.append(oneeteamresult["AVG(Q28)"])
        eteamresult_.append(oneeteamresult["AVG(Q29)"])
        eteamresult_.append(oneeteamresult["AVG(Q30)"])
        eteamresult_.append(oneeteamresult["AVG(Q31)"])
    print(eteamresult_)

    einnovationresult_ = []
    for oneeinnovationresult in einnovationresult:
        einnovationresult_.append(oneeinnovationresult["AVG(Q32)"])
        einnovationresult_.append(oneeinnovationresult["AVG(Q33)"])
        einnovationresult_.append(oneeinnovationresult["AVG(Q34)"])
        einnovationresult_.append(oneeinnovationresult["AVG(Q35)"])
        einnovationresult_.append(oneeinnovationresult["AVG(Q36)"])
        einnovationresult_.append(oneeinnovationresult["AVG(Q37)"])
        einnovationresult_.append(oneeinnovationresult["AVG(Q38)"])
    print(einnovationresult_)

    ehappinnessresult_ = []
    for oneehappinessresult in ehappinnessresult:
        ehappinnessresult_.append(oneehappinessresult["AVG(Q39)"])
        ehappinnessresult_.append(oneehappinessresult["AVG(Q40)"])
    print(ehappinnessresult_)



    avgmtasksresult = float(sum(mtasksresult_)) / len(mtasksresult_)
    avgmmanagerresult = float(sum(mmanagerresult_)) / len(mmanagerresult_)
    avgmvisionresult = float(sum(mvisionresult_)) / len(mvisionresult_)
    avgmteamresult = float(sum(mteamresult_)) / len(mteamresult_)
    avgminnovationresult = float(sum(minnovationresult_)) / len(minnovationresult_)
    avgmhappinnessresult = float(sum(mhappinnessresult_)) / len(mhappinnessresult_)
    print(avgmhappinnessresult)


    avgetasksresult = float(sum(etasksresult_)) / len(etasksresult_)
    avgemanagerresult = float(sum(emanagerresult_)) / len(emanagerresult_)
    avgevisionresult = float(sum(evisionresult_)) / len(evisionresult_)
    avgeteamresult = float(sum(eteamresult_)) / len(eteamresult_)
    avgeinnovationresult = float(sum(einnovationresult_)) / len(evisionresult_)
    avgehappinnessresult = float(sum(ehappinnessresult_)) / len(ehappinnessresult_)


    return render_template("manager_view_report.html", manager_name=manager_name, avgmtasksresult=avgmtasksresult,\
    avgmmanagerresult=avgmmanagerresult, avgmvisionresult=avgmvisionresult, avgmteamresult=avgmteamresult, \
    avgminnovationresult=avgminnovationresult, avgmhappinnessresult=avgmhappinnessresult,\
    avgetasksresult=avgetasksresult, avgemanagerresult=avgemanagerresult, avgevisionresult=avgevisionresult,\
    avgeteamresult=avgeteamresult, avgeinnovationresult=avgeinnovationresult, avgehappinnessresult=avgehappinnessresult)


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
