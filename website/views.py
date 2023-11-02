from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
from .models import Continent, Country, City

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')#Gets the note from the HTML 

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)  #providing the schema for the note 
            db.session.add(new_note) #adding the note to the database 
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

@views.route('/continents', methods=['GET'])
@login_required
def continents():
    continents = Continent.query.all()
    return render_template('continents.html', continents=continents, user=current_user)

@views.route('/countries', methods=['GET'])
@login_required
def view_countries():
    countries = Country.query.all()
    # Assuming Continent is another model
    continents = {continent.continent_id: continent.continent_name for continent in Continent.query.all()}
    
    # Define the function within the route handler
    def get_continent_name(id):
        return continents.get(id)

    return render_template('countries.html', countries=countries, get_continent_name=get_continent_name, user=current_user)

@views.route('/cities', methods=['GET'])
@login_required
def cities():
    cities = City.query.all()
    return render_template('cities.html', cities=cities, user=current_user)

