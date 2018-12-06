Design document

Our website is designed to enable managers to receive an easy assessment of their leadership style, so that they can lead their team in the
best way and know how to use their strengths and work on their weaknesses in their leadership position.

We decided to enable anyone who wants to evaluate their leadership skills to register on our website. We store the email and hashed password
used for the registration in an SQL table named users that includes these components, as well as their id and full name and since they
registered, they will be entered as managers in our table.

The managers are then directed to the manager homepage of the website after registering, just like after logging in. The homepage has a short
text explaining the steps to take to get their leadership style assessed. The first one should be to enter emails of feedback givers on the
„request feedback website“. The feedback givers are then automatically emailed with a message requesting them to give feedback for this manager
(the name that they registered with is used) and their login credentials. These consist of their email address and a randomly generated password.
Again, this data is entered automatically after a manager requests feedback, into our users table. This time the password is automatically set
and the hashed password is entered without the employee setting it. The employee is registered as a feedback giver and it is noted to whom he
is giving feedback.

We decided to not make it possible to enter an employee address twice. This is to prevent one from requesting multiple feedback from one person
and thereby deluding the result. It is furthermore not allowed to request feedback from an employee who is already giving feedback to another
manager. This is again to not delude the result since an employee then already knows the survey when taking it the second time and additionally,
due to this design a manager is not able to better his result by reregistering and asking the same feedback givers. To make sure this isn’t
possible we configured the users table in a way that the “email_address” field is a unique field.

After submitting the emails of feedback givers, the manager can see the status of his requests on the homepage.

The next step for a manger is to provide self-evaluation of his leadership skills. He does so on the „self-assessment“ page that he can access
through the navigation bar. The self-assessment contains the same survey as the employees see when logging in to their employee accounts. The
survey asks 40 questions about the leadership style and offers a select button with different options on how much they agree with the statement.
The answers to these questions are entered into a data table called „surveyanswers“. In this table, depending on the selected option, a value
between 1 and 5 is entered. Additionally, to the 40 values to the 40 questions the user id and the id of the manager they are giving feedback
to (if it is a self-assessment these to values will match) is entered.

The survey can only be submitted when all questions are answered (there is client side and server side protection). We implemented this in order
to receive the best result for the report.

Finally, once both the self-assessment and external assessment are submitted, the „view report“ page shows a full report on the leadership
style of the manager. The report starts with a short explanation for the manager how to read the report. It then gives him an overall score
of his leadership skills which we calculated by assessing all 40 questions. The overall score can be broken down into different categories to
which again different questions are used to assess the scores. All these calculations we did in our python code. We then write the results for
the categories to CSV files in order to visualize them with d3 into a bar chart.
