from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, ProfileType, City, Country, Continent
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
from passlib.hash import scrypt

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        entered_password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if scrypt.verify(entered_password,user.password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    # get cities, countries, continents to pass to the form for values in the drop down lists.
    cities = City.query.all()
    countries = Country.query.all()
    continents = Continent.query.all()

    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        #profile_string = request.form.get('profile')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        #print(profile_string)
        selected_city = request.form.get('city')
        print(f"selected_city: {selected_city}")

        city = City.query.filter_by(city_id=selected_city).first()
        print(f"city.city_id: {city.city_id}")
        print(f"city.city_name: {city.city_name}")
        country = Country.query.filter_by(country_id=city.parent_country_id).first()
        print(f"country.country_name: {country.country_name}")
        continent = Continent.query.filter_by(continent_id=country.parent_continent_id).first()
        print(f"country.parent_continent_name: {continent.continent_name}")

        #try:
        #    profile_enum = ProfileType[ProfileType.EMPLOYEE]
        #except KeyError:
            # Handle the case where the input string doesn't match any enum value
            # You can raise an exception, set a default value, or handle it as needed.
        #    profile_enum = ProfileType.EMPLOYEE  # Default to EMPLOYEE in this example

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            hashed_password = scrypt.hash(password1)
            new_user = User(email=email, first_name=first_name, last_name=last_name, 
                password=hashed_password, from_city_id=city.city_id, 
                from_country_id=country.country_id, from_continent_id=continent.continent_id)

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", cities=cities, countries=countries, continents=continents, user=current_user)