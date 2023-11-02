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
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    profile = db.Column(db.Enum(ProfileType),default=ProfileType.EMPLOYEE)
    notes = db.relationship('Note') ## here Note is the name of the class Note (not the table), therefore Uppercase as first letter
    was_assessed_by = db.relationship('Assessment')
    ## has_assessed = db.relationship('Assessment')
    

class SkillArea(db.Model):
    __tablename__ = 'table_areas'
    area_id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(150), unique=True)
    area_description = db.Column(db.String(1000))
    child_categories = db.relationship('SkillCategory')
    defaultArea = db.Column(db.Boolean,default=False)

class SkillCategory(db.Model):
    __tablename__ = 'table_categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(150), unique=True)
    category_description = db.Column(db.String(1000))
    child_skills = db.relationship('Skill')
    parent_area = db.Column(db.Integer, db.ForeignKey('table_areas.area_id'))
    defaultCategory = db.Column(db.Boolean,default=False)


class Skill(db.Model):
    __tablename__ = 'table_skills'
    skill_id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(150), unique=True)
    skill_description = db.Column(db.String(1000))
    skill_category = db.Column(db.Integer, db.ForeignKey('table_categories.category_id'))
    assessed_by = db.relationship('Assessment')

class Assessment(db.Model):
    __tablename__ = 'table_assessments'
    assess_id = db.Column(db.Integer, primary_key=True)
    assess_date = db.Column(db.DateTime(timezone=True), default=func.now())
    proficiency_level = db.Column(db.Enum(ProficiencyLevel),default=0)
    assess_comment = db.Column(db.String(150))
    for_skill = db.Column(db.Integer, db.ForeignKey('table_skills.skill_id'))
    for_user = db.Column(db.Integer, db.ForeignKey('user.id')) ## the user who gets the assessment
    ## assessed_by = db.Column(db.Integer, db.ForeignKey('user.id')) ## the user who gives the assessment
    ## for_user_ref = db.relationship('User', foreign_keys='for_user') ## the alias on relationship to user who gets the assessment
    ## assessed_by_ref = db.relationship('User', foreign_keys='assessed_by') ## the alias on relationship to user who gives the assessment
