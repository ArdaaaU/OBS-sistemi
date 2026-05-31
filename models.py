from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'academician', 'student'
    name = db.Column(db.String(100), nullable=False)

    # Relationships
    courses_taught = db.relationship('Course', backref='academician', lazy=True)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    academician_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    max_absenteeism = db.Column(db.Integer, default=20, nullable=False)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    midterm_grade = db.Column(db.Float, nullable=True)
    final_grade = db.Column(db.Float, nullable=True)
    project_grade = db.Column(db.Float, nullable=True)
    presentation_grade = db.Column(db.Float, nullable=True)
    absenteeism = db.Column(db.Integer, default=0)
    
    # A student can only be enrolled in a course once
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),)

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_log'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), nullable=False) # 'Geldi', 'Gelmedi'
    
    student = db.relationship('User', backref='attendance_logs')
    course = db.relationship('Course', backref='attendance_logs')

class Announcement(db.Model):
    __tablename__ = 'announcement'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    academician_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    course = db.relationship('Course', backref='announcements')
    academician = db.relationship('User', backref='announcements')
