from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, User, SkillArea, SkillCategory, SkillGroup, Skill, Assessment, ProficiencyLevel, Qualification
from . import db
import json
from .models import Continent, Country, City, ProfileType
import pandas as pd
from passlib.hash import scrypt
from collections import Counter
from sqlalchemy import or_


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

@views.route('/skills')
def display_skill_inventory():
    return render_template("skills.html", user=current_user, list_skills=Skill.query.all())

@views.route('/continents', methods=['GET'])
@login_required
def view_continents():
    continents = Continent.query.all()
    list_all_users = User.query.all()

    return render_template('continents.html', continents=continents, user=current_user, list_all_users=list_all_users)

@views.route('/countries', methods=['GET'])
@login_required
def view_countries():
    countries = Country.query.all()
    list_all_users = User.query.all()
    continents = {continent.continent_id: continent.continent_name for continent in Continent.query.all()}
    
    def get_continent_name(id):
        return continents.get(id)
    return render_template('countries.html', countries=countries, get_continent_name=get_continent_name, user=current_user, list_all_users=list_all_users)

@views.route('/cities', methods=['GET'])
@login_required
def view_cities():
    cities = City.query.all()
    list_all_users = User.query.all()
    names_of_countries = {country.country_id: country.country_name for country in Country.query.all()}

    # Define from which country is the city
    def get_country_name(a_country_id):
        return names_of_countries.get(a_country_id)

    return render_template('cities.html', cities=cities, get_country_name=get_country_name, user=current_user, list_all_users=list_all_users)

@views.route('/people', methods=['GET'])
@login_required
def view_users():
    users = User.query.all()
    cities = {city.city_id: city.city_name for city in City.query.all()}

    def get_city_name_from_user(id):
        return cities.get(id)

    return render_template('people.html', get_city_name_from_user=get_city_name_from_user, users=users, user=current_user)

@views.route('/proficiencies', methods=['GET'])
@login_required
def display_proficiency_matrix():
    
    # Get all users and skills
    list_all_users = User.query.all()
    #list_all_skills = Skill.query.all()
    #selected_group_id = 1  # Replace this with the group_id you want to filter by
    selected_group = SkillGroup.query.filter_by(default_group=True).first()
    if selected_group:
        selected_group_id = selected_group.group_id
    else:
        # Handle the case where no SkillGroup has default_group set to True
        selected_group_id = 2  # You can choose an appropriate default value or error handling strategy

    list_all_skills = Skill.query.filter_by(parent_group=selected_group_id).all()


    # Create an empty matrix with users IDs as rows and skills IDs as columns
    proficiency_matrix = pd.DataFrame(0, index=[a_user.id for a_user in list_all_users], columns=[a_skill.skill_id for a_skill in list_all_skills])

    # Fill in the matrix with proficiency values
    list_all_assessments = Assessment.query.all()
    for an_assessment in list_all_assessments:
        for_user = an_assessment.for_user
        for_skill = an_assessment.for_skill
        proficiency = int(an_assessment.proficiency_level.value)
        proficiency_matrix.at[for_user, for_skill] = proficiency

    return render_template('proficiencies.html', list_all_skills=list_all_skills, list_all_users=list_all_users, matrix=proficiency_matrix, user=current_user)

@views.route('/init-10-users', methods=['GET'])
def create10users():
    for i in range(1, 11):
        emailX = f"username{i}@gmail.com"
        first_nameX = f"username{i}"
        last_nameX = f"username{i}"
        hashed_passwordX = scrypt.hash(f"username{i}")
        new_userX = User(email=emailX, first_name=first_nameX, last_name=last_nameX, password=hashed_passwordX)
        db.session.add(new_userX)
        db.session.commit()
    flash('10 Accounts created!', category='success')
    
    return render_template("home.html", user=current_user)

@views.route('/user_proficiencies', methods=['GET', 'POST'])
@login_required  # Make sure the user is logged in to access this page
def user_proficiencies():
    if request.method == 'POST':
        # Handle the form submission and update proficiency levels
        for skill_id in request.form:
            proficiency_level = request.form[skill_id]
            assessment = Assessment.query.filter_by(for_skill=skill_id, for_user=current_user.id).first()
            if assessment:
                assessment.proficiency_level = ProficiencyLevel(int(proficiency_level))
                db.session.commit()
    
    list_skills = Skill.query.all()
    assessments = Assessment.query.filter_by(for_user=current_user.id).all()
    proficiency_levels = {assessment.for_skill: assessment.proficiency_level.value for assessment in assessments}
    # Calculate proficiency level counts
    proficiency_counts = Counter(proficiency_levels.values())

    return render_template('user_proficiencies.html', user=current_user, list_skills=list_skills, proficiency_levels=proficiency_levels, proficiency_counts=proficiency_counts)

@views.route('/proficiency_spider/<int:user_id>', methods=['GET', 'POST'])
@login_required  # Make sure the user is logged in to access this page
def proficiency_spider(user_id):
    selected_user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        # Handle the form submission and update proficiency levels
        for skill_id in request.form:
            proficiency_level = request.form[skill_id]
            assessment = Assessment.query.filter_by(for_skill=skill_id, for_user=selected_user.id).first()
            if assessment:
                assessment.proficiency_level = ProficiencyLevel(int(proficiency_level))
                db.session.commit()
    
    list_skills = Skill.query.all()
    assessments = Assessment.query.filter_by(for_user=selected_user.id).all()
    proficiency_levels = {assessment.for_skill: assessment.proficiency_level.value for assessment in assessments}

    return render_template('proficiency_spider.html', user=current_user, list_skills=list_skills, proficiency_levels=proficiency_levels, selected_user=selected_user)

@views.route('/delete_city/<int:city_id>', methods=['POST'])
@login_required
def delete_city(city_id):
    city = City.query.get(city_id)
    
    if city:
        # Check if the number of users is 0
        if len(city.city_members) == 0:
            db.session.delete(city)
            db.session.commit()
            flash('City' 'deleted!', category='success')
   
    return redirect(url_for('views.view_cities'))

@views.route('/display_user/<int:user_id>', methods=['GET'])
@login_required
def display_user(user_id):
    selected_user = User.query.get_or_404(user_id)

    continents = {continent.continent_id: continent.continent_name for continent in Continent.query.all()}
    countries = {country.country_id: country.country_name for country in Country.query.all()}
    cities = {city.city_id: city.city_name for city in City.query.all()}
    # Define the function within the route handler
    def get_continent_name_from_user(id):
        return continents.get(id)
    def get_country_name_from_user(id):
        return countries.get(id)
    def get_city_name_from_user(id):
        return cities.get(id)
    return render_template('display_user.html', get_continent_name_from_user=get_continent_name_from_user, get_country_name_from_user=get_country_name_from_user, get_city_name_from_user=get_city_name_from_user, user=current_user, selected_user=selected_user)

@views.route('/update_user', methods=['GET', 'POST'])
@login_required
def update_user():
    continents = {continent.continent_id: continent.continent_name for continent in Continent.query.all()}
    countries = {country.country_id: country.country_name for country in Country.query.all()}
    cities_ids = {city.city_id: city.city_name for city in City.query.all()}
    cities = City.query.all()
    # Define the function within the route handler
    def get_continent_name_from_user(id):
        return continents.get(id)
    def get_country_name_from_user(id):
        return countries.get(id)
    def get_city_name_from_user(id):
        return cities_ids.get(id)

    if request.method == 'POST':

        current_user.first_name = request.form['firstname']
        current_user.last_name = request.form['lastname']
        current_user.profile = ProfileType(int(request.form['profile']))

        # Assuming you have a foreign key relationship set up in your User model
        current_user.from_city = City.query.get(int(request.form['city']))

        db.session.commit()

        return redirect(url_for('update_user.html'), cities=cities, user=current_user)
    return render_template('update_user.html', get_continent_name_from_user=get_continent_name_from_user, get_country_name_from_user=get_country_name_from_user, get_city_name_from_user=get_city_name_from_user, cities=cities, user=current_user)

    # Handle other cases as needed
    return render_template('error.html', error='Invalid Request')

@views.route('/locations')
def locations():
    continents = Continent.query.all()
    countries = Country.query.all()
    cities = City.query.all()

    return render_template('locations.html', continents=continents, countries=countries, cities=cities, user=current_user)

@views.route('/skills_directory')
def display_skills_directory():
    areas = SkillArea.query.all()
    categories = SkillCategory.query.all()
    groups = SkillGroup.query.all()
    skills = Skill.query.all()

    return render_template('skills_directory.html', areas=areas, categories=categories, groups=groups, skills=skills, user=current_user)

@views.route('/people_finder', methods=['GET', 'POST'])
def people_finder():
    skills = Skill.query.all()
    cities = {city.city_id: city.city_name for city in City.query.all()}
    # Define the function within the route handler
    def get_city_name_from_user(id):
        return cities.get(id)
    def get_proficiency_for_skill_from_user(id):
        return cities.get(id)

    if request.method == 'POST':
        skill_id_1 = request.form.get('skill1')
        skill_id_1 = int(skill_id_1)
        min_proficiency_1 = request.form.get('min_proficiency1')
        min_proficiency_1 = int(min_proficiency_1)
        skill_id_2 = request.form.get('skill2')
        skill_id_2 = int(skill_id_2)
        min_proficiency_2 = request.form.get('min_proficiency2')
        min_proficiency_2 = int(min_proficiency_2)

        level_mapping = {
            5: [ProficiencyLevel.FIVE],
            4: [ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            3: [ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            2: [ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            1: [ProficiencyLevel.ONE, ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            0: [ProficiencyLevel.ZERO, ProficiencyLevel.ONE, ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
        }

        allowed_levels_1 = level_mapping.get(min_proficiency_1, [])
        allowed_levels_2 = level_mapping.get(min_proficiency_2, [])

        query_filters = []
        query_filters.append(
                db.and_(
                    Assessment.for_skill == skill_id_1,
                    Assessment.proficiency_level.in_(allowed_levels_1)
                )
            )
        query_filters.append(
                db.and_(
                    Assessment.for_skill == skill_id_2,
                    Assessment.proficiency_level.in_(allowed_levels_2)
                )
            )
        base_query = User.query.join(Assessment)
        for query_filter in query_filters:
                base_query = base_query.filter(query_filter)
        matching_users = base_query.all()

        matching_users_1 = User.query.join(Assessment).filter(
            Assessment.for_skill == skill_id_1,
            Assessment.proficiency_level.in_(allowed_levels_1),
        ).all()
        matching_users_2 = User.query.join(Assessment).filter(
            Assessment.for_skill == skill_id_2,
            Assessment.proficiency_level.in_(allowed_levels_2),
        ).all()

        # Extract user IDs from each list
        user_ids_1 = {user.id for user in matching_users_1}
        user_ids_2 = {user.id for user in matching_users_2}

        # Find the intersection of user IDs
        common_user_ids = user_ids_1.intersection(user_ids_2)

        # Build a new list of users that have common IDs
        common_users = [user for user in matching_users_1 if user.id in common_user_ids]

        # 'common_users' now contains the users that are present in both lists based on their IDs

        return render_template('people_finder.html', skills=skills, users=common_users, user=current_user,
                               selected_skill_1=skill_id_1, selected_min_proficiency_1=min_proficiency_1, selected_skill_2=skill_id_2, selected_min_proficiency_2=min_proficiency_2, get_city_name_from_user=get_city_name_from_user)

    return render_template('people_finder.html', skills=skills, user=current_user)

@views.route('/qualifications', methods=['GET', 'POST'])
def user_qualifications():
    user = current_user

    if request.method == 'POST':
        # Handle the form submission for adding/editing qualifications
        qualification_id = request.form.get('qualification_id')
        qualification_name = request.form.get('qualification_name')
        # Add other fields as needed

        if qualification_id:
            # Editing an existing qualification
            qualification = Qualification.query.get_or_404(qualification_id)
            qualification.qualification_name = qualification_name
            # Update other fields as needed
        else:
            # Adding a new qualification
            new_qualification = Qualification(
                qualification_name=qualification_name,
                # Set other fields as needed
            )
            user.qualifications.append(new_qualification)
        
        db.session.commit()

    return render_template('qualifications.html', user=current_user)