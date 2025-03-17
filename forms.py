from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, RadioField, DateField, TimeField, DecimalField, SubmitField
from wtforms.validators import InputRequired, EqualTo

class SearchServicesForm(FlaskForm):
    service_name = StringField("Search service: ",
                               default="")
    submit = SubmitField("Search")

class RegistrationForm(FlaskForm):
    username = StringField("User id: ",
                          validators=[InputRequired()])
    password = PasswordField("Password: ",
                             validators=[InputRequired()])
    password2 = PasswordField("Confirm password: ",
                              validators=[InputRequired(), EqualTo("password")])
    account_type = RadioField("Account Type: ",
                              choices=["Customer","Seller"],
                              default="Customer")
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("User id: ",
                          validators=[InputRequired()])
    password = PasswordField("Password: ",
                             validators=[InputRequired()])
    submit = SubmitField("Login")

class MakeBookingForm(FlaskForm):
    date = DateField("Date: ",
                     validators=[InputRequired()])
    from_when = TimeField("From: ",
                          validators=[InputRequired()])
    till_when = TimeField("Till: ",
                          validators=[InputRequired()])
    promo_code = StringField("Do you have a promo code? ")
    submit = SubmitField("Proceed to payment")

class ApplyPromoCodeForm(FlaskForm):
    promo_code = StringField("Promo Code: ",
                             validators=[InputRequired()])
    submit = SubmitField("Apply Discount")

class MakePaymentForm(FlaskForm):
    address = StringField("Address: ",
                        validators=[InputRequired()])
    price = DecimalField("Price: ")
    confirm = RadioField("Confirm payment",
                         choices=["Yes","No"],
                         default="No")
    submit = SubmitField("Pay")

class CancelBookingForm(FlaskForm):
    confirm = RadioField("Confirm payment",
                         choices=["Yes","No"],
                         default="No")
    reason = StringField("Reason: ",
                         validators=[InputRequired()])
    submit = SubmitField("Cancel Booking")

class ReportForm(FlaskForm):
    report_username = StringField("Report against username: ",
                           validators=[InputRequired()])
    reason = StringField("Reason (Please put the booking id in as well if applicable): ",
                         validators=[InputRequired()])
    submit = SubmitField("Report")

class UpdateAvailabilityForm(FlaskForm):
    date = DateField("Date: ",
                     validators=[InputRequired()])
    from_when = TimeField("From: ",
                          validators=[InputRequired()])
    till_when = TimeField("Till: ",
                          validators=[InputRequired()])
    submit = SubmitField("Update")

class UploadServiceForm(FlaskForm):
    service_name = StringField("Service Name: ",
                               validators=[InputRequired()])
    description = StringField("Description: ",
                              validators=[InputRequired()])
    promo_code = StringField("Promo Code: ")
    promo_discount = DecimalField("Promo Discount: ",
                                  default=0.15)
    max_booking_hrs = IntegerField("Max Booking Hours: ",
                                   default=2)
    price_per_hour = DecimalField("Price Per Hour: ",
                                  validators=[InputRequired()])
    submit = SubmitField("Upload")

class ChangeDescForm(FlaskForm):
    service_code = IntegerField("Service Code: ",
                                validators=[InputRequired()])
    new_desc = StringField("Enter new description: ",
                           validators=[InputRequired()])
    submit = SubmitField("Update")

class AddPromoForm(FlaskForm):
    service_code = IntegerField("Service Code: ",
                                validators=[InputRequired()])
    promo_code = StringField("Promo Code: ",
                             validators=[InputRequired()])
    promo_discount = DecimalField("Promo Discount: ",
                                  default=0.15)
    submit = SubmitField("Add")

class DeletePromoForm(FlaskForm):
    service_code = IntegerField("Service Code: ",
                                validators=[InputRequired()])
    confirm = RadioField("Are you sure you want to delete the promo code?",
                         choices=["Yes","No"],
                         default="No")
    submit = SubmitField("Delete")

class ChangeMaxHrsForm(FlaskForm):
    service_code = IntegerField("Service Code: ",
                                validators=[InputRequired()])
    new_max_hrs = IntegerField("New Max Booking Hours: ",
                               validators=[InputRequired()])
    submit = SubmitField("Update")

class ChangePriceForm(FlaskForm):
    service_code = IntegerField("Service Code: ",
                                validators=[InputRequired()])
    new_price = DecimalField("New Price: ",
                               validators=[InputRequired()])
    submit = SubmitField("Update")

class RemoveServiceForm(FlaskForm):
    service_code = IntegerField("Service Code: ",
                                validators=[InputRequired()])
    confirm = RadioField("Are you sure you want to delete this service?",
                         choices=["Yes","No"],
                         default="No")
    submit = SubmitField("Delete")

class SuspendAccountForm(FlaskForm):
    confirm = RadioField("Suspend account?",
                         choices=["Yes","No"],
                         default="No")
    submit = SubmitField("Suspend")

class DeleteReportForm(FlaskForm):
    confirm = RadioField("Delete Report?",
                         choices=["Yes","No"],
                         default="No")
    submit = SubmitField("Delete")