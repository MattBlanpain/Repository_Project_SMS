from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, User, SkillArea, SkillCategory, SkillGroup, Skill, Assessment, ProficiencyLevel, Qualification
from . import db
import json
from .models import Continent, Country, City, ProfileType
import pandas as pd
from passlib.hash import scrypt
from collections import Counter
from sqlalchemy import and_
import plotly.graph_objs as go
import plotly.express as px
import plotly
import os
import secrets
from PIL import Image
from .forms import RegistrationForm, LoginForm, UpdateAccountForm
import sys

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    users = User.query.all()
    cities = City.query.all()
    countries = Country.query.all()
    skills = Skill.query.all()
    if request.method == 'POST': 
        note = request.form.get('note')#Gets the note from the HTML 

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)  #providing the schema for the note 
            db.session.add(new_note) #adding the note to the database 
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user, users=users, skills=skills, cities=cities, countries=countries)

@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    #return jsonify({})
    return render_template("note.html", user=current_user)


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

@views.route('/proficiencies', methods=['GET', 'POST'])
@login_required
def display_proficiency_matrix():
    list_all_users = User.query.all()
    list_all_skills = Skill.query.all()

    # Fetch available groups for dropdown
    available_groups = SkillGroup.query.all()

    # Fetch available categories for dropdown
    available_categories = SkillCategory.query.all()

    selected_group_id = request.args.get('group')  # Get the selected group from URL parameters
    selected_category_id = request.args.get('category')  # Get the selected category from URL parameters

    if selected_group_id and selected_group_id != "all":
        # Filter skills by selected group
        list_all_skills = Skill.query.filter_by(parent_group=selected_group_id).all()
        selected_group_id= int(selected_group_id)


    if selected_category_id and selected_category_id != "all":
        # Filter skills by selected category (fetching all groups in the category)
        groups_in_category = SkillGroup.query.filter_by(parent_category=selected_category_id).all()
        group_ids_in_category = [group.group_id for group in groups_in_category]
        list_all_skills = Skill.query.filter(Skill.parent_group.in_(group_ids_in_category)).all()
        selected_category_id= int(selected_category_id)

    proficiency_matrix = pd.DataFrame(0, index=[a_user.id for a_user in list_all_users], columns=[a_skill.skill_id for a_skill in list_all_skills])

    list_all_assessments = Assessment.query.all()
    for an_assessment in list_all_assessments:
        for_user = an_assessment.for_user
        for_skill = an_assessment.for_skill
        proficiency = int(an_assessment.proficiency_level.value)
        proficiency_matrix.at[for_user, for_skill] = proficiency
    
    return render_template('proficiencies.html', list_all_skills=list_all_skills, list_all_users=list_all_users, matrix=proficiency_matrix, user=current_user, available_groups=available_groups, available_categories=available_categories, selected_group_id=selected_group_id, selected_category_id=selected_category_id)

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
@login_required
def proficiency_spider(user_id):
    selected_user = User.query.get_or_404(user_id)

    # Fetch all groups for the dropdown list
    groups = SkillGroup.query.all()

    # Fetch all categories for the dropdown list
    categories = SkillCategory.query.all()

    # Fetch all skills for the radar chart
    list_skills = Skill.query.all()

    if request.method == 'POST':
        # Handle filter by group
        group_filter = request.form.get('group_filter')
        if group_filter and group_filter != 'all':
            filtered_skills = Skill.query.filter_by(parent_group=group_filter).all()
        else:
            filtered_skills = list_skills

        # Handle filter by category
        category_filter = request.form.get('category_filter')
        if category_filter and category_filter != 'all':
            groups_in_category = SkillGroup.query.filter_by(parent_category=category_filter).all()
            group_ids_in_category = [group.group_id for group in groups_in_category]
            filtered_skills = [skill for skill in filtered_skills if skill.parent_group in group_ids_in_category]

    else:
        # When first loading the page or resetting filters
        filtered_skills = list_skills

    # Fetch proficiency levels based on the filtered skills for the selected user
    assessments = Assessment.query.filter_by(for_user=selected_user.id).all()
    proficiency_levels = {assessment.for_skill: assessment.proficiency_level.value for assessment in assessments if assessment.for_skill in [skill.skill_id for skill in filtered_skills]}
    print (proficiency_levels)
    return render_template('proficiency_spider.html', user=current_user, list_skills=list_skills, filtered_skills=filtered_skills, proficiency_levels=proficiency_levels, selected_user=selected_user, groups=groups, categories=categories)

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
        #current_user.profile = ProfileType(int(request.form['profile']))

        # Assuming you have a foreign key relationship set up in your User model
        current_user.from_city_id = int(request.form['city'])

        db.session.commit()

        #return redirect(url_for('update_user.html'), cities=cities, user=current_user)
        return render_template('update_user.html', get_continent_name_from_user=get_continent_name_from_user, get_country_name_from_user=get_country_name_from_user, get_city_name_from_user=get_city_name_from_user, cities=cities, current_city_id=current_user.from_city_id, user=current_user)

    # Handle other cases as needed
    return render_template('update_user.html', get_continent_name_from_user=get_continent_name_from_user, get_country_name_from_user=get_country_name_from_user, get_city_name_from_user=get_city_name_from_user, cities=cities, current_city_id=current_user.from_city_id, user=current_user)

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
    groups = SkillGroup.query.all()
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
        skill_id_3 = request.form.get('skill3')
        skill_id_3 = int(skill_id_3)
        min_proficiency_3 = request.form.get('min_proficiency3')
        min_proficiency_3 = int(min_proficiency_3)
        skill_id_4 = request.form.get('skill4')
        skill_id_4 = int(skill_id_4)
        min_proficiency_4 = request.form.get('min_proficiency4')
        min_proficiency_4 = int(min_proficiency_4)
        skill_id_5 = request.form.get('skill5')
        skill_id_5 = int(skill_id_5)
        min_proficiency_5 = request.form.get('min_proficiency5')
        min_proficiency_5 = int(min_proficiency_5)

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
        allowed_levels_3 = level_mapping.get(min_proficiency_3, [])
        allowed_levels_4 = level_mapping.get(min_proficiency_4, [])
        allowed_levels_5 = level_mapping.get(min_proficiency_5, [])

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
        query_filters.append(
                db.and_(
                    Assessment.for_skill == skill_id_3,
                    Assessment.proficiency_level.in_(allowed_levels_3)
                )
            )
        query_filters.append(
                db.and_(
                    Assessment.for_skill == skill_id_4,
                    Assessment.proficiency_level.in_(allowed_levels_4)
                )
            )
        query_filters.append(
                db.and_(
                    Assessment.for_skill == skill_id_5,
                    Assessment.proficiency_level.in_(allowed_levels_5)
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
        matching_users_3 = User.query.join(Assessment).filter(
            Assessment.for_skill == skill_id_3,
            Assessment.proficiency_level.in_(allowed_levels_3),
        ).all()
        matching_users_4 = User.query.join(Assessment).filter(
            Assessment.for_skill == skill_id_4,
            Assessment.proficiency_level.in_(allowed_levels_4),
        ).all()
        matching_users_5 = User.query.join(Assessment).filter(
            Assessment.for_skill == skill_id_5,
            Assessment.proficiency_level.in_(allowed_levels_5),
        ).all()

        # Extract user IDs from each list
        user_ids_1 = {user.id for user in matching_users_1}
        user_ids_2 = {user.id for user in matching_users_2}
        user_ids_3 = {user.id for user in matching_users_3}
        user_ids_4 = {user.id for user in matching_users_4}
        user_ids_5 = {user.id for user in matching_users_5}

        # Find the intersection of user IDs
        common_user_ids_1_2 = user_ids_1.intersection(user_ids_2)
        common_user_ids_1_2_3 = common_user_ids_1_2.intersection(user_ids_3)
        common_user_ids_1_2_3_4 = common_user_ids_1_2_3.intersection(user_ids_4)
        common_user_ids_1_2_3_4_5 = common_user_ids_1_2_3_4.intersection(user_ids_5)

        # Build a new list of users that have common IDs
        common_users = [user for user in matching_users_1 if user.id in common_user_ids_1_2_3_4_5]

        # 'common_users' now contains the users that are present in both lists based on their IDs

        return render_template('people_finder.html', skills=skills, groups=groups, users=common_users, user=current_user,
                               selected_skill_1=skill_id_1, selected_min_proficiency_1=min_proficiency_1, selected_skill_2=skill_id_2, selected_min_proficiency_2=min_proficiency_2, selected_skill_3=skill_id_3, selected_min_proficiency_3=min_proficiency_3,selected_skill_4=skill_id_4, selected_min_proficiency_4=min_proficiency_4,selected_skill_5=skill_id_5, selected_min_proficiency_5=min_proficiency_5, get_city_name_from_user=get_city_name_from_user)

    return render_template('people_finder.html', skills=skills, groups=groups, user=current_user)

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

@views.route('/bubble_chart', methods=['GET', 'POST'])
def bubble_chart():
    skill_groups = SkillGroup.query.all()  # Fetch all skill groups for dropdown

    if request.method == 'POST':
        selected_group_id = request.form.get('group')  # Get selected group ID
        selected_proficiency = int(request.form.get('proficiency', ProficiencyLevel.TWO.value))  # Default to 2 if not selected

        # Fetch skills with user counts having proficiency >= selected_proficiency for the selected group
        skills_with_counts = get_skills_with_user_counts(int(selected_proficiency), selected_group_id)

        return render_template('bubble_chart.html', bubble_data=skills_with_counts, selected_proficiency=selected_proficiency, skill_groups=skill_groups, selected_group_id=selected_group_id, user=current_user)
    else:
        # Default to proficiency level 2 and display all skills (no group filter)
        skills_with_counts = get_skills_with_user_counts(ProficiencyLevel.TWO.value)
        return render_template('bubble_chart.html', bubble_data=skills_with_counts, selected_proficiency=ProficiencyLevel.TWO.value, skill_groups=skill_groups, selected_group_id='', user=current_user)

def get_skills_with_user_counts(proficiency_level, group_id=None):
    skills_with_counts = {}
    skills_query = Skill.query

    if group_id:
        skills_query = skills_query.filter_by(parent_group=group_id)

    skills = skills_query.all()
    level_mapping = {
            5: [ProficiencyLevel.FIVE],
            4: [ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            3: [ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            2: [ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            1: [ProficiencyLevel.ONE, ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            0: [ProficiencyLevel.ZERO, ProficiencyLevel.ONE, ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
        }

    allowed_levels = level_mapping.get(proficiency_level, [])

    for skill in skills:
        users_with_proficiency = Assessment.query.filter_by(for_skill=skill.skill_id).filter(Assessment.proficiency_level.in_(allowed_levels)).count()
        skills_with_counts[skill.skill_name] = users_with_proficiency
    
    return skills_with_counts

@views.route('/sunburst_chart', methods=['GET', 'POST'])
def sunburst_chart():

    skill_groups = SkillGroup.query.all()  # Fetch all skill groups for dropdown
    selected_proficiency = int(request.form.get('selected_proficiency', ProficiencyLevel.TWO.value))  # Default to 2 if not selected
    selected_group_id = request.form.get('group')  # Get selected group ID


    if request.method == 'POST':
        selected_group_id = request.form.get('group')  # Get selected group ID

        # Fetch skills with user counts having proficiency >= selected_proficiency for the selected group
        skills_with_counts = get_skills_with_user_counts(int(selected_proficiency), selected_group_id)
        return render_template('sunburst_chart.html', chart_fig=chart_fig, selected_proficiency=selected_proficiency, skill_groups=skill_groups, selected_group_id=selected_group_id, user=current_user)
    else:
        # Default to proficiency level 2 and display all skills (no group filter)
        skills_with_counts = get_skills_with_user_counts(ProficiencyLevel.TWO.value)
    skills_data = db.session.query(Skill.skill_name, SkillGroup.group_name, SkillCategory.category_name, SkillArea.area_name) \
        .join(SkillGroup, Skill.parent_group == SkillGroup.group_id) \
        .join(SkillCategory, SkillGroup.parent_category == SkillCategory.category_id) \
        .join(SkillArea, SkillCategory.parent_area == SkillArea.area_id) \
        .join(Assessment, Assessment.for_skill == Skill.skill_id) \
        .filter(Assessment.proficiency_level >= int(selected_proficiency)) \
        .all()

    # Aggregate data for the Sunburst chart
    skills = {}
    for skill, group, category, area in skills_data:
        if skill not in skills:
            skills[skill] = {}
        if group not in skills[skill]:
            skills[skill][group] = {}
        if category not in skills[skill][group]:
            skills[skill][group][category] = []
        skills[skill][group][category].append(area)

    # Generate data for the Sunburst chart
    labels = ['Area', 'Category', 'Group', 'Skill']
    parents = ['', 'Area', 'Category', 'Group']
    values = []
    colors = ['#f2f2f2', '#e6e6e6', '#cccccc', '#b3b3b3']

    for skill, groups in skills.items():
        values.append(len(groups))  # Considering number of groups per skill

        for group, categories in groups.items():
            values.append(len(categories))  # Considering number of categories per group

            for category, areas in categories.items():
                values.append(len(areas))  # Considering number of areas per category

                # Uncomment below to include skills (number of users with proficiency >= selected_proficiency)
                # values.append(len(areas))  # Considering number of skills with proficiency >= selected_proficiency

    trace = go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues='total',
        marker=dict(colors=colors),
    )

    layout = go.Layout(
        title='Sunburst Chart',
        margin=dict(l=0, r=0, b=0, t=40),
    )

    chart_data = [trace]
    chart_fig = go.Figure(data=chart_data, layout=layout)

    return render_template('sunburst_chart.html', chart_fig=chart_fig, selected_proficiency=int(selected_proficiency), skill_groups=skill_groups, selected_group_id=selected_group_id, user=current_user)

def get_skills_with_user_counts(proficiency_level, group_id=None):
    skills_with_counts = {}
    skills_query = Skill.query

    if group_id:
        skills_query = skills_query.filter_by(parent_group=group_id)

    skills = skills_query.all()
    level_mapping = {
            5: [ProficiencyLevel.FIVE],
            4: [ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            3: [ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            2: [ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            1: [ProficiencyLevel.ONE, ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            0: [ProficiencyLevel.ZERO, ProficiencyLevel.ONE, ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
        }

    allowed_levels = level_mapping.get(proficiency_level, [])

    for skill in skills:
        users_with_proficiency = Assessment.query.filter_by(for_skill=skill.skill_id).filter(Assessment.proficiency_level.in_(allowed_levels)).count()
        skills_with_counts[skill.skill_name] = users_with_proficiency
    
    return skills_with_counts

@views.route('/sunburst', methods=['GET', 'POST'])
def sunburst():

    selected_min_prof = int(request.args.get('selected_min_prof', 2))

    list_skills = Skill.query.all()  # Fetch all skills for the sunburst chart

    d = []
    for s in list_skills:
        skill_name = s.skill_name
        skill_group = s.get_group_name_for_skill()
        skill_category = s.get_category_name_for_skill()
        skill_area = s.get_area_name_for_skill()
        nb_users = int(get_nb_users_with_prof_for_skill(s,selected_min_prof))

        d.append(
            {
                'skill':skill_name,
                'group':skill_group,
                'category':skill_category,
                'area':skill_area,
                'nb_users':nb_users
            }
        )

    df=pd.DataFrame(d)

    rslt_df_without_0 = df[df['nb_users'] != 0] # remove skills with nb user is 0

    # Create chart
    fig = px.sunburst(
        data_frame=rslt_df_without_0,
        path=['area', 'category', 'group', 'skill'],  # Root, branches, leaves
        values='nb_users',
        color='nb_users',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_traces(textinfo='label+value')
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    # Create graphJSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
     
    # Use render_template to pass graphJSON to html
    return render_template('sunburst.html', graphJSON=graphJSON, user=current_user, selected_min_prof=selected_min_prof)

def get_nb_users_with_prof_for_skill(a_skill, proficiency_level):
    level_mapping = {
            5: [ProficiencyLevel.FIVE],
            4: [ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            3: [ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            2: [ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            1: [ProficiencyLevel.ONE, ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
            0: [ProficiencyLevel.ZERO, ProficiencyLevel.ONE, ProficiencyLevel.TWO, ProficiencyLevel.THREE, ProficiencyLevel.FOUR, ProficiencyLevel.FIVE],
        }
    allowed_levels = level_mapping.get(proficiency_level, [])
    nb_users = Assessment.query.filter_by(for_skill=a_skill.skill_id).filter(Assessment.proficiency_level.in_(allowed_levels)).count()
    
    return nb_users

@views.route('/user_sunburst/<int:user_id>', methods=['GET', 'POST'])
def user_sunburst(user_id):

    selected_user = User.query.get_or_404(user_id)  # Get selected user from user ID
    list_skills = Skill.query.all()  # Fetch all skills for the sunburst chart

    d = []
    for s in list_skills:
        skill_name = s.skill_name
        skill_group = s.get_group_name_for_skill()
        skill_category = s.get_category_name_for_skill()
        skill_area = s.get_area_name_for_skill()
        skill_proficiency = selected_user.proficiency_for_skill(s.skill_id)
        skill_proficiency = str(skill_proficiency)

        d.append(
            {
                'skill':skill_name,
                'group':skill_group,
                'category':skill_category,
                'area':skill_area,
                'size':int(1),
                'proficiency':str(skill_proficiency)
            }
        )

    pd.DataFrame(d)

    # Create chart
    fig = px.sunburst(
        data_frame=d,
        path=['area', 'category', 'group', 'skill'],  # Root, branches, leaves
        values='size',
        color='proficiency',
        color_discrete_map={'(?)':'#32FF32','0':'#000', '1':'#05106E', '2':'#0A37A6', '3':'#007DFF', '4':'#0CA4EB', '5':'#0DE0FF'}
    )

    fig.update_traces(textinfo='label')
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
))
    #fig.update_layout(sunburstcolorway = px.colors.qualitative.Pastel)

    # Create graphJSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
     
    # Use render_template to pass graphJSON to html
    return render_template('user_sunburst.html', graphJSON=graphJSON, user=current_user, selected_user=selected_user)

@views.route('/globe', methods=['GET', 'POST'])
def globe():

    countries = Country.query.all()
        
    d = []
    for c in countries:
        country_name = c.country_name
        continent_name = c.get_continent_name()
        country_iso = c.country_iso
        nb_users = c.get_user_count()

        d.append(
            {
                'country':country_name,
                'continent':continent_name,
                'iso_alpha':country_iso,
                'users':nb_users
            }
        )

    pd.DataFrame(d)

    fig = px.scatter_geo(d, locations="iso_alpha",
                        color="continent", # which column to use to set the color of markers
                        hover_name="country", # column added to hover information
                        size="users", # size of markers
                        projection="orthographic")

    fig2 = px.choropleth (d, locations='iso_alpha',
                          color='users',
                          hover_name='country', 
                          #animation_frame='year',
                          color_continuous_scale=px.colors.sequential.Plasma,
                          projection='natural earth') 
    
    
    # Create graphJSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Create graphJSON
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
     
    # Use render_template to pass graphJSON to html
    return render_template('globe.html', graphJSON=graphJSON, graphJSON2=graphJSON2, user=current_user)

@views.route('/note', methods=['GET', 'POST'])
@login_required
def note():
    if request.method == 'POST': 
        note = request.form.get('note')#Gets the note from the HTML 

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)  #providing the schema for the note 
            db.session.add(new_note) #adding the note to the database 
            db.session.commit()
            flash('Enhancement Request added!', category='success')

    return render_template("note.html", user=current_user)



def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext

    fn = getattr(sys.modules['__main__'], '__file__')
    root_path = os.path.abspath(os.path.dirname(fn))
    picture_path = os.path.join(root_path, 'website/static/profile_pics', picture_fn)

    #cwd = os.getcwd()  # Get the current working directory (cwd)
    #files = os.listdir(cwd)  # Get all the files in that directory
    #print("Files in %r: %s" % (cwd, files))

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@views.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('views.account'))
        #return render_template('account.html', title='Account', image_file=image_file, form=form, user=current_user)
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    print(image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form, user=current_user)

@views.route('/user/<int:user_id>', methods=['GET'])
@login_required
def user(user_id):
    selected_user = User.query.get_or_404(user_id)
    continents = {continent.continent_id: continent.continent_name for continent in Continent.query.all()}
    countries = {country.country_id: country.country_name for country in Country.query.all()}
    cities = {city.city_id: city.city_name for city in City.query.all()}

    # Calculate proficiency counts for each level
    assessments = Assessment.query.filter_by(for_user=selected_user.id).all()
    proficiency_levels = {assessment.for_skill: assessment.proficiency_level.value for assessment in assessments}
    proficiency_counts = Counter(proficiency_levels.values())

    # Define the function within the route handler
    def get_continent_name_from_user(id):
        return continents.get(id)
    def get_country_name_from_user(id):
        return countries.get(id)
    def get_city_name_from_user(id):
        return cities.get(id)
    return render_template('user.html', get_continent_name_from_user=get_continent_name_from_user, get_country_name_from_user=get_country_name_from_user, get_city_name_from_user=get_city_name_from_user, user=current_user, selected_user=selected_user, proficiency_counts=proficiency_counts)

@views.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():

    # Fetch all groups for the dropdown list
    groups = SkillGroup.query.all()

    # Fetch all categories for the dropdown list
    categories = SkillCategory.query.all()

    # Fetch all skills
    list_skills = Skill.query.all()
    total_skills = len(list_skills)

    if request.method == 'POST':
        # Handle filter by group
        group_filter = request.form.get('group_filter')
        if group_filter and group_filter != 'all':
            filtered_skills = Skill.query.filter_by(parent_group=group_filter).all()
            filtered_by_group = "yes"
            filtered_by_category = "no"
        else:
            filtered_skills = list_skills
            filtered_by_group = "no"
            filtered_by_category = "no"


        # Handle filter by category
        category_filter = request.form.get('category_filter')
        if category_filter and category_filter != 'all':
            groups_in_category = SkillGroup.query.filter_by(parent_category=category_filter).all()
            group_ids_in_category = [group.group_id for group in groups_in_category]
            filtered_skills = [skill for skill in filtered_skills if skill.parent_group in group_ids_in_category]
            filtered_by_category = "yes"
            filtered_by_group = "no"
        else:
            filtered_by_category = "no"


    else:
        # When first loading the page or resetting filters
        filtered_skills = list_skills
        filtered_by_group = "no"
        filtered_by_category = "no"
        group_filter = 'all'
        category_filter = 'all'

    # Fetch proficiency levels based on the filtered skills for the selected user
    assessments = Assessment.query.filter_by(for_user=current_user.id).all()
    proficiency_levels = {assessment.for_skill: assessment.proficiency_level.value for assessment in assessments if assessment.for_skill in [skill.skill_id for skill in filtered_skills]}
 
    proficiency_levels = {assessment.for_skill: assessment.proficiency_level.value for assessment in assessments}
    proficiency_counts = Counter(proficiency_levels.values())

    return render_template('assessment.html', user=current_user, total_skills=total_skills, list_skills=filtered_skills, proficiency_levels=proficiency_levels, proficiency_counts=proficiency_counts, groups=groups, categories=categories, filtered_by_group=filtered_by_group, filtered_by_category=filtered_by_category, selected_category_id=category_filter, selected_group_id=group_filter)

@views.route('/update_proficiencies', methods=['POST'])
@login_required
def update_proficiencies():
    # Handle the form submission and update proficiency levels
    for skill_id in request.form:
        proficiency_level = request.form[skill_id]
        print(skill_id)
        print(proficiency_level)
        assessment = Assessment.query.filter_by(for_skill=skill_id, for_user=current_user.id).first()
        if assessment:
            assessment.proficiency_level = ProficiencyLevel(int(proficiency_level))
            db.session.commit()
    
    return redirect(url_for('views.assessment'))

@views.route('/backlog', methods=['GET'])
@login_required
def backlog():
    users = User.query.all()
    notes = Note.query.all()
    
    return render_template('backlog.html', user=current_user,notes=notes, users=users)
