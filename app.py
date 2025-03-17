from flask import Flask, render_template, session, redirect, url_for, g, request
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import forms
from functools import wraps
from datetime import date
# import matplotlib

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "secret-tunnel-secret-tunnel"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# checks if a user in logged in (code done in class)
@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)
    g.account_type = session.get("account_type", None)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

# Creating an account (code done in class)
@app.route("/register", methods=["GET","POST"])     # EVERYONE
def register():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        account_type = form.account_type.data
        account_type = account_type.upper()
        db = get_db()
        clash = db.execute("""SELECT * FROM login_accounts
                           WHERE username = ?;""", 
                           (username,)).fetchone()
        if clash is not None:
            form.username.errors.append("Username already taken")
        else:
            db.execute("""INSERT INTO login_accounts (username,password,account_type)
                       VALUES (?,?,?);""",
                       (username,generate_password_hash(password),account_type))
            db.commit()
            return redirect( url_for("login") )
    return render_template("register.html", 
                            form = form)

# logging into your account (code done in class)
@app.route("/login", methods=["GET","POST"])    # EVERYONE
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        db = get_db()
        username_in_db = db.execute("""SELECT * FROM login_accounts
                           WHERE username = ?;""", 
                           (username,)).fetchone()
        account_type = db.execute("""SELECT account_type FROM login_accounts
                            WHERE username = ?;""",
                            (username,)).fetchone()
        account_type = list(account_type)
        if username_in_db is None:
            form.username.errors.append("No such username")
        elif username_in_db[3]:
            form.username.errors.append("This account has been suspended.")
        elif account_type[0] == "ADMIN":
            if username_in_db["password"] == password:
                session.clear()
                session["user_id"] = username
                session["account_type"] = account_type[0]
                session.modified = True
                return redirect( url_for("view_reports") )
        elif not check_password_hash(username_in_db["password"], password):
            form.password.errors.append("Incorrect password!")
        else:
            session.clear()
            session["user_id"] = username
            session["account_type"] = account_type
            session.modified = True
            if account_type[0] == "CUSTOMER":
                next_page = request.args.get("next")
                if not next_page:
                    next_page = url_for("index")
                return redirect(next_page)
            elif account_type[0] == "SELLER":
                return redirect( url_for("timetable") )
    return render_template("login.html", form = form)

# main page / first page that shows up (code done in class)
@app.route("/", methods=["GET","POST"])     # GENERAL / CUSTOMER
def index():        # displays all services bases on a search
    form = forms.SearchServicesForm()
    db = get_db()
    services = db.execute("""SELECT * FROM services;""")
    if form.validate_on_submit():
        service_name = form.service_name.data
        if service_name != "":
            services = list(db.execute("""SELECT * FROM services
                                WHERE service_name LIKE ?;""",
                                (service_name,)).fetchall())
    return render_template("search_services.html", form = form, services = services)

@app.route("/view_a_service/<service_code>")    # CUSTOMER
def view_a_service(service_code):   # displays a services' details
    db = get_db()
    service_details = db.execute("""SELECT * FROM services
                                 WHERE service_code = ?;""",
                                 (service_code,)).fetchone()
    return render_template("view_a_service.html", service_details = service_details)

@app.route("/make_booking/<max_hrs>/<service_code>", methods=["GET","POST"])    # CUSTOMER
@login_required
def make_booking(max_hrs,service_code):     # allows the customer to choose a time slot for booking
    form = forms.MakeBookingForm()
    how_long = None
    if form.validate_on_submit():
        booking_date = str(form.date.data)
        from_when = str(form.from_when.data)
        till_when = str(form.till_when.data)
        db = get_db()
        how_long = list(db.execute("""SELECT round((julianday(?) - julianday(?))*24);""",
                              (booking_date+till_when, booking_date+from_when)).fetchone())
        clash1 = db.execute("""SELECT * FROM booking_details
                           WHERE date = ?
                           AND ( (? > from_when AND ? < till_when)
                           OR (? > from_when AND ? < till_when) );""",
                           (booking_date,from_when,from_when,till_when,till_when)).fetchone()
        clash2 = db.execute("""SELECT * FROM seller_availability
                            WHERE date = ?
                            AND ( (? > from_when AND ? < till_when)
                            OR (? > from_when AND ? < till_when) );""",
                            (booking_date,from_when,from_when,till_when,till_when)).fetchone()
        if how_long[0] > float(max_hrs):
            form.till_when.errors.append("Can only book for max. of "+max_hrs+" hours at a time.")
        elif clash1 or clash2:
            form.from_when.errors.append("Seller is already booked / not available during this time slot.")
        else:
            return redirect( url_for('make_payment', service_code = service_code, booking_date = booking_date, from_when = from_when, till_when = till_when) )
    return render_template("make_booking.html", form = form)

@app.route("/make_payment/<service_code>/<booking_date>/<from_when>/<till_when>", methods=["GET","POST"])   # CUSTOMER
@login_required
def make_payment(service_code, booking_date, from_when, till_when):     # allows the customer to make payment
    form1 = forms.ApplyPromoCodeForm()
    form2 = forms.MakePaymentForm()
    discount = 0
    db = get_db()
    price_per_hour = list(db.execute("""SELECT price_per_hour FROM services
                       WHERE service_code = ?;""",
                       (service_code,)).fetchone())[0]
    how_long = list(db.execute("""SELECT round((julianday(?) - julianday(?))*24);""",
                              (booking_date+till_when, booking_date+from_when)).fetchone())
    price = price_per_hour * float(how_long[0])
    seller_code = list(db.execute("""SELECT seller_code FROM services
                                  WHERE service_code = ?;""",
                                  (service_code,)).fetchone())[0]
    if form1.validate_on_submit():
        promo_code = form1.promo_code.data
        valid = db.execute("""SELECT * FROM services
                           WHERE promo_code = ?
                           AND service_code = ?;""",
                           (promo_code,service_code)).fetchone()
        if not valid:
            form1.promo_code.errors.append("Invalid Promo code")
        else:
            discount = valid[5]
            price = price - (price*discount)
    elif form2.validate_on_submit():
        address = form2.address.data
        db.execute("""INSERT INTO booking_details (service_code,customer_username,address,seller_code,date,from_when,till_when,price)
                   VALUES (?,?,?,?,?,?,?);""",
                   (service_code,session["user_id"],address,seller_code,booking_date,from_when,till_when,price))
        db.commit()
        booking_id = list(db.execute("""SELECT booking_id FROM booking_details
                                     WHERE service_code = ?
                                     AND booking_date = ?
                                     AND from_when = ?;""",
                                     (service_code,booking_date,from_when)))
        return redirect( url_for('receipt', booking_id) )
    return render_template("make_payment.html", form1 = form1, form2 = form2, price = price)

@app.route("/receipt/<booking_id>")     # CUSTOMER
@login_required
def receipt(booking_id):    # allows the customer to view their receipt
    db = get_db()
    booking_details = db.execute("""SELECT bd.booking_id,bd.service_code,s.service_name,bd.address,bd.date,bd.from_when,bd.till_when,bd.price,seller_code
                                 FROM booking_details AS bd JOIN services AS s
                                 ON bd.service_code = s.service_code
                                 WHERE booking_id = ?;""",
                                 (booking_id,)).fetchone()
    return render_template("receipt.html", booking_details = booking_details)

@app.route("/cancel_booking/<booking_id>", methods=["GET","POST"])   # CUSTOMER / SELLER
@login_required
def cancel_booking(booking_id):   # allows the customer / seller to cancel a booking
    form = forms.CancelBookingForm()
    if form.validate_on_submit():
        confirm = form.confirm.data
        if confirm == "Yes":
            reason = form.reason.data
            account_type = session['account_type']
            db = get_db()
            db.execute("""INSERT INTO cancelled_bookings
                       VALUES (?,?,?)""",
                       (booking_id,account_type,reason))
            db.commit()
        return redirect( url_for("view_bookings") )
    return render_template("cancel_booking.html", form = form)

@app.route("/view_bookings")     # CUSTOMER / SELLER
@login_required
def view_bookings():     # displays booking details
    username = session['user_id']
    db = get_db()
    upcoming_bookings = db.execute("""SELECT bd.booking_id,bd.service_code,s.service_name,bd.date,bd.from_when,bd.till_when,bd.customer_username
                                   FROM booking_details AS bd JOIN services AS s
                                   ON bd.service_code = s.service_code
                                   WHERE date >= DATE('now')
                                   AND bd.customer_username = ?
                                   AND booking_id NOT IN 
                                   (
                                        SELECT booking_id FROM cancelled_bookings
                                   );""",
                                   (username,)).fetchall()
    past_bookings = db.execute("""SELECT bd.booking_id,bd.service_code,s.service_name,bd.date,bd.customer_username
                                   FROM booking_details AS bd JOIN services AS s
                                   ON bd.service_code = s.service_code
                                   WHERE date < DATE('now')
                                   AND bd.customer_username = ?
                                   AND booking_id NOT IN 
                                   (
                                        SELECT booking_id FROM cancelled_bookings
                                   );""",
                                   (username,)).fetchall()
    cancelled_bookings = db.execute("""SELECT bd.booking_id,bd.service_code,s.service_name,bd.date,bd.customer_username
                                   FROM booking_details AS bd JOIN services AS s
                                   ON bd.service_code = s.service_code
                                   WHERE bd.customer_username = ?
                                   AND booking_id IN 
                                   (
                                        SELECT booking_id FROM cancelled_bookings
                                   );""",
                                   (username,)).fetchall()
    return render_template("bookings.html", upcoming_bookings = upcoming_bookings, past_bookings = past_bookings, cancelled_bookings = cancelled_bookings)

@app.route("/report", methods=["GET","POST"])       # CUSTOMER / SELLER
@login_required
def report():       # report a customer or seller
    form = forms.ReportForm()
    username = session["user_id"]
    message = None
    db = get_db()
    if form.validate_on_submit():
        report_username = form.report_username.data
        exists = db.execute("""SELECT * FROM login_accounts
                            WHERE username = ?;""",
                            (report_username,)).fetchone()
        if not exists:
            form.report_username.errors.append("This Username does not exist.")
        else:
            reason = form.reason.data
            today = str(date.today())
            db.execute("""INSERT INTO reports_table (report_reason,reported_by,got_reported,date)
                        VALUES (?,?,?,?)""",
                        (reason,username,report_username,today))
            db.commit()
            message = "Done!"
    return render_template("report.html", form = form, message = message)

@app.route("/timetable")     # SELLER
@login_required
def timetable():    # displays the sellers timetable for the next week
    username = session["user_id"]
    db = get_db()
    today = date.today()
    bookings = db.execute("""SELECT bd.booking_id, bd.from_when, bd.till_when, s.service_name, bd.customer_username
                          FROM booking_details as bd JOIN services as s JOIN seller_details as sd
                          ON bd.service_code = s.service_code
                          AND bd.seller_code = sd.seller_code
                          WHERE sd.seller_name = ?
                          AND bd.date > ?;""",
                          (username, today)).fetchall()
    return render_template("timetable.html", bookings = bookings)

@app.route("/update_my_availability", methods=["GET","POST"])   # SELLER
@login_required
def update_my_availability():   # The seller can update their availability if they have another event
    form = forms.UpdateAvailabilityForm()
    date_unavailable = None
    from_when = None
    till_when = None
    if form.validate_on_submit():
        date_unavailable = form.date.data
        from_when = str(form.from_when.data)
        till_when = str(form.till_when.data)
        username = session["user_id"]
        db = get_db()
        clash1 = db.execute("""SELECT booking_id, from_when, till_when FROM booking_details
                            WHERE date = ?
                            AND ( (? > from_when AND ? < till_when)
                            OR (? > from_when AND ? < till_when) )""",
                            (date_unavailable, from_when, from_when, till_when, till_when)).fetchone()
        clash2 = db.execute("""SELECT from_when, till_when FROM seller_availability
                            WHERE date = ?
                            AND ( (? > from_when AND ? < till_when)
                            OR (? > from_when AND ? < till_when) )""",
                            (date_unavailable, from_when, from_when, till_when, till_when)).fetchone()
        if clash1:
            form.from_when.errors.append("You already have a booking from "+clash1[1]+" till "+clash1[2]+". Booking ID: "+clash1[0])
        elif clash2:
            form.from_when.errors.append("You have already blocked out your schedule from "+clash2[0]+" till "+clash2[1]+". If you wish to take more till off please enter the timings correctly.")
        else:
            db.execute("""INSERT INTO seller_availability
                       VALUES (?,?,?,?);""",
                       (username,date_unavailable,from_when,till_when))
            db.commit()
            return redirect( url_for('timetable') )
    return render_template("update_availability.html", form = form, from_when = from_when, till_when = till_when, date_unavailable = date_unavailable)

@app.route("/view_my_services")     # SELLER
@login_required
def view_my_services():     # They can view the services they offer and update from there(another route)
    db = get_db()
    username = session["user_id"]
    services = db.execute("""SELECT service_code, service_name, description, promo_code, promo_discount, max_booking_hrs, price_per_hour
                          FROM services
                          WHERE seller_code = ?;""",
                          (username,)).fetchall()
    return render_template("view_services.html", services = services)

@app.route("/upload_service", methods=["GET","POST"])   # SELLER
@login_required
def upload_service():   # lets the seller add a service
    form = forms.UploadServiceForm()
    if form.validate_on_submit():
        service_name = form.service_name.data
        description = form.description.data
        promo_code = form.promo_code.data
        promo_discount = float(form.promo_discount.data)
        max_booking_hrs = int(form.max_booking_hrs.data)
        price_per_hour = float(form.price_per_hour.data)
        username = session["user_id"]
        db = get_db()
        if promo_code:
            db.execute("""INSERT INTO services (service_name,description,seller_code,promo_code,promo_discount,max_booking_hrs,price_per_hour)
                       VALUES (?,?,?,?,?,?,?);""",
                       (service_name,description,username,promo_code,promo_discount,max_booking_hrs,price_per_hour))
        else:
            db.execute("""INSERT INTO services (service_name,description,seller_code,max_booking_hrs,price_per_hour)
                       VALUES (?,?,?,?,?);""",
                       (service_name,description,username,max_booking_hrs,price_per_hour))
        db.commit()
        return redirect( url_for('view_my_services') )
    return render_template("upload_service.html", form = form)

@app.route("/update_service")   # SELLER
@login_required
def update_service():   # lets the seller update a service a part of a service
    return render_template("update_service.html")

@app.route("/change_desc", methods=["GET","POST"])      # SELLER
@login_required
def change_desc():      # change the description of a service
    form = forms.ChangeDescForm()
    message = None
    if form.validate_on_submit():
        service_code = form.service_code.data
        new_desc = form.new_desc.data
        db = get_db()
        clash = db.execute("""SELECT * FROM services
                            WHERE service_code = ?;""",
                            (service_code,)).fetchone()
        if clash:
            form.service_code.errors.append("Invalid service code")
        else:
            db.execute("""UPDATE services
                       SET desc = ?
                       WHERE service_code = ?;""",
                       (new_desc,service_code))
            db.commit()
            message = "Description has been updated!"
    return render_template("change_desc.html", form = form, message = message)

@app.route("/add_promo_code", methods=["GET","POST"])       # SELLER
@login_required
def add_promo_code():       # add a promo code to a service
    form = forms.AddPromoForm()
    message = None
    if form.validate_on_submit():
        service_code = form.service_code.data
        promo_code = form.promo_code.data
        promo_discount = float(form.promo_discount.data)
        db = get_db()
        clash1 = db.execute("""SELECT * FROM services
                            WHERE service_code = ?;""",
                            (service_code,)).fetchone()
        clash2 = db.execute("""SELECT promo_code FROM services
                           WHERE service_code = ?;""",
                           (service_code,)).fetchone()
        if clash1:
            form.service_code.errors.append("Invalid service code")
        elif clash2:
            form.service_code.errors.append("This service already has a promo code.")
        else:
            db.execute("""UPDATE services
                       SET promo_code = ?, promo_discount = ?
                       WHERE service_code = ?;""",
                       (promo_code,promo_discount,service_code))
            db.commit()
            message = "Promo code has been added!"
    return render_template("add_promo_code.html", form = form, message = message)

@app.route("/delete_promo_code", methods=["GET","POST"])        # SELLER
@login_required
def delete_promo_code():        # delete a promo code
    form = forms.DeletePromoForm()
    message = None
    if form.validate_on_submit():
        service_code = form.service_code.data
        confirm = form.confirm.data
        db = get_db()
        clash = db.execute("""SELECT * FROM services
                            WHERE service_code = ?;""",
                            (service_code,)).fetchone()
        if clash:
            form.service_code.errors.append("Invalid service code")
        else:
            if confirm == "Yes":
                db.execute("""DELETE promo_code FROM services 
                        WHERE service_code = ?;""",
                        (service_code,))
                db.commit()
                message = "Deleted Promo code!"
    return render_template("delete_promo_code.html", form = form, message = message)

@app.route("/change_max_hrs", methods=["GET","POST"])       # SELLER
@login_required
def change_max_hrs():       # change the max booking hrs for a service
    form = forms.ChangeMaxHrsForm()
    message = None
    if form.validate_on_submit():
        service_code = form.service_code.data
        new_max_hrs = int(form.new_max_hrs.data)
        db = get_db()
        clash = db.execute("""SELECT * FROM services
                            WHERE service_code = ?;""",
                            (service_code,)).fetchone()
        if clash:
            form.service_code.errors.append("Invalid service code")
        else:
            db.execute("""UPDATE services
                       SET max_booking_hrs = ?
                       WHERE service_code = ?;""",
                       (new_max_hrs,service_code))
            db.commit()
            message = "Successfully changed max booking hrs!"
    return render_template("change_max_hrs.html", form = form, message = message)

@app.route("/change_price", methods=["GET","POST"])     # SELLER
@login_required
def change_price():     # change a service price per hour
    form = forms.ChangePriceForm()
    message = None
    if form.validate_on_submit():
        service_code = form.service_code.data
        new_price = float(form.new_price.data)
        db = get_db()
        clash = db.execute("""SELECT * FROM services
                            WHERE service_code = ?;""",
                            (service_code,)).fetchone()
        if clash:
            form.service_code.errors.append("Invalid service code")
        else:
            db.execute("""UPDATE services
                       SET price_per_hour = ?
                       WHERE service_code = ?;""",
                       (new_price,service_code))
            db.commit()
            message = "Successfully changed price!"
    return render_template("change_price.html", message  = message)

@app.route("/remove_service", methods=["GET","POST"])    # SELLER
@login_required
def remove_service():   # lets the seller take down or remove a service
    form = forms.RemoveServiceForm()
    if form.validate_on_submit():
        service_code = form.service_code.data
        confirm = form.confirm.data
        if confirm == "Yes":
            db = get_db()
            db.execute("""DELETE FROM services WHERE service_code = ?;""",
                       (service_code,))
            db.commit()
        return redirect( url_for('view_my_services') )
    return render_template("remove_service.html", form = form)

@app.route("/all_payments")     # ADMIN
@login_required
def payments():     # can view all payments
    db = get_db()
    upcoming_bookings = db.execute("""SELECT bd.booking_id,bd.service_code,s.service_name,bd.customer_username,bd.address,bd.seller_code,bd.date,bd.from_when,bd.till_when,bd.price
                                   FROM booking_details AS bd JOIN services AS s
                                   ON bd.service_code = s.service_code
                                   WHERE date >= DATE('now')
                                   AND booking_id NOT IN 
                                   (
                                        SELECT booking_id FROM cancelled_bookings
                                   );""").fetchall()
    past_bookings = db.execute("""SELECT bd.booking_id,bd.service_code,s.service_name,bd.customer_username,bd.address,bd.seller_code,bd.date,bd.from_when,bd.till_when,bd.price
                                   FROM booking_details AS bd JOIN services AS s
                                   ON bd.service_code = s.service_code
                                   WHERE date < DATE('now')
                                   AND booking_id NOT IN 
                                   (
                                        SELECT booking_id FROM cancelled_bookings
                                   );""").fetchall()
    cancelled_bookings = db.execute("""SELECT bd.booking_id,bd.service_code,s.service_name,bd.customer_username,bd.address,bd.seller_code,bd.date,bd.from_when,bd.till_when,bd.price,cb.cancelled_by_whom,cb.reason
                                   FROM booking_details AS bd JOIN services AS s JOIN cancelled_bookings AS cb
                                   ON bd.service_code = s.service_code
                                   AND bd.booking_id = cb.booking_id;""").fetchall()
    return render_template("payments.html", upcoming_bookings = upcoming_bookings, past_bookings = past_bookings, cancelled_bookings = cancelled_bookings)

@app.route("/view_reports")    # ADMIN
@login_required
def view_reports():      # displays the admins stats
    db = get_db()
    reports = db.execute("""SELECT * FROM reports_table
                        ORDER BY date;""")
    return render_template("view_reports.html", reports = reports)

@app.route("/suspend_account/<report_id>")      # ADMIN
@login_required
def suspend_account(report_id):     # suspend an account or delete a report
    form1 = forms.SuspendAccountForm()
    form2 = forms.DeleteReportForm()
    db = get_db()
    report_details = db.execute("""SELECt * FROM reports_table
                                WHERE report_id = ?;""",
                                (report_id,)).fetchone()
    if form1.validate_on_submit():
        if form1.confirm.data == "Yes":
            db.execute("""UPDATE login_accounts
                       SET account_status = 'SUSPENDED'
                       WHERE username = ?;""",
                       (report_details[4],))
            db.execute("""DELETE FROM reports_table
                       WHERE report_id = ?;""",
                       (report_details[0],))
            db.commit()
            return redirect( url_for('view_reports') )
    elif form2.validate_on_submit():
        if form2.confirm.date == "Yes":
            db.execute("""DELETE FROM reports_table
                       WHERE report_id = ?;""",
                       (report_details[0],))
            db.commit()
            return redirect( url_for('view_reports') )
    return render_template("suspend_account.html", report_details = report_details, form1 = form1, form2 = form2)

@app.route("/stats")    # ADMIN
@login_required
def stats():
    db = get_db()
    return render_template("stats.html")

# logging out of your account (code done in class)
@app.route("/logout")
def logout():
    session.clear()
    session.modified = True
    return redirect( url_for("index") )