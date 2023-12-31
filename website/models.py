from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from enum import Enum

class ProfileType(Enum):
    EMPLOYEE = 1
    MANAGER = 2
    ADMIN = 3

class ProficiencyLevel(Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    
class Note(db.Model): ## a class must have Uppercase as first letter
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) ## here user is the name of the table of users, a table must have lowercase as first letter

class User(db.Model, UserMixin): ## a class must have Uppercase as first letter
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(20))
    last_name = db.Column(db.String(20))
    profile = db.Column(db.Enum(ProfileType),default=ProfileType.EMPLOYEE)
    image_file = db.Column(db.String(20), default='default.jpg')
    is_supervised_by = db.relationship('User')
    is_supervisor_of = db.Column(db.Integer, db.ForeignKey('user.id'))
    #hired_on = db.Column(db.DateTime(timezone=True), default=func.now())
    #registered_on = db.Column(db.DateTime(timezone=True), default=func.now())
    #job_title = db.Column(db.String(150))
    notes = db.relationship('Note') ## here Note is the name of the class Note (not the table), therefore Uppercase as first letter
    was_assessed_by = db.relationship('Assessment')
    #was_assessed_by = db.relationship('Assessment', backref='user', foreign_keys='Assessment.for_user')
    # has_assessed = db.relationship('Assessment')
    from_continent_id = db.Column(db.Integer, db.ForeignKey('table_continents.continent_id'))
    from_country_id = db.Column(db.Integer, db.ForeignKey('table_countries.country_id'))
    from_city_id = db.Column(db.Integer, db.ForeignKey('table_cities.city_id'))
    def proficiency_percentage(self, proficiency_level):
        total_assessments = len(self.assessments)
        print(total_assessments)
        if total_assessments == 0:
            return 0
        proficiency_count = sum(1 for assessment in self.assessments if assessment.proficiency_level == proficiency_level)
        return (proficiency_count / total_assessments) * 100
    def get_top_skills(self):
        # Get the user's assessments ordered by proficiency level in descending order
        sorted_assessments = sorted(self.assessments, key=lambda x: x.proficiency_level.value, reverse=True)

        # Take the top 10 assessments
        top_skills = sorted_assessments[:10]

        # Create a list of tuples with skill and proficiency
        result = [(assessment.skill, assessment.proficiency_level.name) for assessment in top_skills]
        return result
    def proficiency_for_skill(self, skill_id):
        assessment = Assessment.query.filter_by(for_user=self.id, for_skill=skill_id).first()
        if assessment:
            return assessment.proficiency_level.value  # Assuming proficiency_level is an Enum
        return 0  # Or handle the case where there's no assessment for the user and skill
    def __repr__(self):
        return f"User('{self.firstname}', '{self.fullname}', '{self.image_file}')"
    
class SkillArea(db.Model):
    __tablename__ = 'table_areas'
    area_id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(150), unique=True)
    default_area = db.Column(db.Boolean,default=False)
    child_categories = db.relationship('SkillCategory')

class SkillCategory(db.Model):
    __tablename__ = 'table_categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(150), unique=True)
    default_category = db.Column(db.Boolean,default=False)
    parent_area = db.Column(db.Integer, db.ForeignKey('table_areas.area_id'))
    child_groups = db.relationship('SkillGroup')

class SkillGroup(db.Model):
    __tablename__ = 'table_groups'
    group_id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(150), unique=True)
    default_group = db.Column(db.Boolean,default=False)
    parent_category = db.Column(db.Integer, db.ForeignKey('table_categories.category_id'))
    child_skills = db.relationship('Skill')

class Skill(db.Model):
    __tablename__ = 'table_skills'
    skill_id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(150), unique=True)
    parent_group = db.Column(db.Integer, db.ForeignKey('table_groups.group_id'))
    assessed_by = db.relationship('Assessment', backref='skill')  # added backref

    def get_skill_name(skill_id):
        skill = Skill.query.filter_by(skill_id=skill_id).first()
        if skill:
            return skill.skill_name
        else:
            return None  # Skill ID not found

    def get_group_name_for_skill(self):
        group = SkillGroup.query.filter_by(group_id=self.parent_group).first()
        return group.group_name if group else None

    def get_category_name_for_skill(self):
        group = SkillGroup.query.filter_by(group_id=self.parent_group).first()
        if group:
            category = SkillCategory.query.filter_by(category_id=group.parent_category).first()
            return category.category_name if category else None
        return None

    def get_area_name_for_skill(self):
        group = SkillGroup.query.filter_by(group_id=self.parent_group).first()
        if group:
            category = SkillCategory.query.filter_by(category_id=group.parent_category).first()
            if category:
                area = SkillArea.query.filter_by(area_id=category.parent_area).first()
                return area.area_name if area else None
        return None
    
class Assessment(db.Model):
    __tablename__ = 'table_assessments'
    assess_id = db.Column(db.Integer, primary_key=True)
    assess_date = db.Column(db.DateTime(timezone=True), default=func.now())
    proficiency_level = db.Column(db.Enum(ProficiencyLevel), default=ProficiencyLevel.ZERO)
    assess_comment = db.Column(db.String(150))
    for_skill = db.Column(db.Integer, db.ForeignKey('table_skills.skill_id'))
    for_user = db.Column(db.Integer, db.ForeignKey('user.id'))  # the user who gets the assessment
    user = db.relationship('User', backref='assessments')

class Continent(db.Model):
    __tablename__ = 'table_continents'
    continent_id = db.Column(db.Integer, primary_key=True)
    continent_name = db.Column(db.String(100))
    child_countries = db.relationship('Country')
    continent_members = db.relationship('User')
    def get_user_count(self): # return the number of users who are located in this continent
        return len(self.continent_members)

class Country(db.Model):
    __tablename__ = 'table_countries'
    country_id = db.Column(db.Integer, primary_key=True)
    country_name = db.Column(db.String(100))
    country_iso = db.Column(db.String(5))
    parent_continent_id = db.Column(db.Integer, db.ForeignKey('table_continents.continent_id'))
    child_cities = db.relationship('City')
    country_members = db.relationship('User')
    def get_user_count(self): # return the number of users who are located in this country
        return len(self.country_members)
    def get_continent_name(self): # return the name of the continent which is parent for this country
        continent = Continent.query.filter_by(continent_id=self.parent_continent_id).first()
        continent_name = continent.continent_name
        return continent_name

class City(db.Model):
    __tablename__ = 'table_cities'
    city_id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String(100))
    parent_country_id = db.Column(db.Integer, db.ForeignKey('table_countries.country_id'))
    city_members = db.relationship('User')
    def get_user_count(self): # return the number of users who are located in this city
        return len(self.city_members)

class Qualification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qualification_name = db.Column(db.String(100))
    qualification_status = db.Column(db.String(100))
    qualification_description = db.Column(db.String(500))
    qualification_start_date = db.Column(db.Date)
    qualification_end_date = db.Column(db.Date)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    from_user = db.relationship('User', backref='qualifications')

    def __repr__(self):
        return f'<Qualification {self.qualification_name}>'
