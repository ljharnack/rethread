"""Form definitions. Flask-WTF handles validation and CSRF protection."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DecimalField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

from .models import CATEGORIES, CONDITIONS, SIZES


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 40)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password", "Passwords must match.")]
    )


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class ListingForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=100)])
    brand = StringField("Brand", validators=[Optional(), Length(max=60)])
    category = SelectField("Category", choices=CATEGORIES)
    size = SelectField("Size", choices=SIZES)
    condition = SelectField("Condition", choices=CONDITIONS)
    price = DecimalField("Price (USD)", places=2, validators=[DataRequired(), NumberRange(min=1, max=10000)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    image = FileField("Photo", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only.")])
