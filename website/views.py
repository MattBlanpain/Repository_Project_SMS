from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from .models import Skill
from . import db
import json
import sqlite3

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


@views.route('/create-skill', methods=['POST'])
def create_skill():  
    skill_name_entered = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    if len(skill_name_entered) < 5:
            flash('Skill name is too short!', category='error') 
    else:
        new_skill = Skill(skill_name=skill_name_entered)  #providing the schema for the note 
        db.session.add(new_skill) #adding the skill to the database 
        db.session.commit()
        flash('Skill added!', category='success')

    return jsonify({})


@views.route('/skill')
def display_skill_inventory():
    return render_template("skill.html", user=current_user, list_skills=Skill.query.all())

