from asyncio import DatagramProtocol
from unicodedata import category
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask import request, jsonify
import base64
from itsdangerous import json
from sqlalchemy import null
from sqlalchemy.sql import func
import datetime
app = Flask(__name__)
from sqlalchemy import delete
from sqlalchemy import update
app.config['SECRET_KEY']='secret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:Raikonen04@localhost:5432/course?sslmode=disable' #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://DB_USER:PASSWORD@HOST/DATABASE'
db = SQLAlchemy(app)

class Users(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	name =db.Column(db.String(20), nullable=False)
	role =db.Column(db.String(20), nullable=False)
	passkey =db.Column(db.String(20), nullable=False)
	courses = db.relationship('Coursedata', backref='owner', lazy='dynamic')

class Topic(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	name =db.Column(db.String(50), nullable=False)
	course = db.relationship('Course', backref='ownera', lazy='dynamic')
	
class Course(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	title =db.Column(db.String(50), nullable=False)
	topic_id=db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
	description =db.Column(db.String(50), nullable=True)
	students = db.relationship('Coursedata', backref='ownere', lazy='dynamic')
	
class Prerequisite(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	course_id=db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
	preq_course_id=db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
		
class Status(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	status = db.Column('status',db.String(20), nullable=False)
	statuses = db.relationship('Coursedata', backref='owneru', lazy='dynamic')
class Coursedata(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
	status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=True)


db.create_all()
db.session.commit()


def auth(a):
    
	e = request.headers['Authorization']
	ee = str(e)
	base64_input = ee[6:].encode("ascii") 

	ag = base64.b64decode(base64_input)
	out = ag.decode("ascii")
	c = out.split(':')
	if a == 'name':
		return c[0]
	elif a == 'passkey':
		return c[1]


@app.route('/index')
def index():
    
	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'user':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
		
	
	return 'WELCOME', 201


@app.route('/course', methods=['POST'])
def create_course():
	
	data = request.get_json()
    
	if not 'title' in data or not 'topic_id' in data or not 'description' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400    
	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'teacher':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
		
	u = Course(
			title=data['title'], 
            topic_id=data['topic_id'],
			description = data['description']
		)
	db.session.add(u)
	usa = Course.query.filter_by(title = data['title']).first()
	for i in data['prerequisite']:
		psa = Course.query.filter_by(title = i).first()
		if 'prerequisite' in data:
			u = Prerequisite(
			course_id=usa.id, 
            preq_course_id=psa.id,
			)
		db.session.add(u)
	db.session.commit()
	return {
		'message' : 'success'
	}, 201

@app.route('/course/<id>', methods=['PUT'])
def update_course(id):
	data = request.get_json()
	
	if not 'prerequisite' in data and not 'title' in data  and not 'description' in data:
		return {
			'error': 'Bad Request',
			'message': 'a parameters need to be present'
		}, 400

	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'teacher':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
	s = Course.query.filter_by(id=id).first_or_404()
	if 'prerequisite' in data:
		s.prerequisite=data.get('prerequisite', Course.prerequisite)
	if 'title' in data:
		s.title=data.get('title', Course.title)
	if 'description' in data:
		s.description=data.get('description', Course.description)

	db.session.commit()
	return {
		'message': 'success'
		}, 201

@app.route('/enroll', methods=['POST'])
def enroll_course():
	
	data = request.get_json()
    
	if not 'title' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400    
	
	title = Course.query.filter_by(title = data['title']) .first()
		
	if not title:
		return jsonify({
			'error': 'Bad Request',
			'message': 'no course found'
		}), 400		
	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'user':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
	
	course = Course.query.filter_by(title = data['title']).first()
	a = Coursedata.query.filter((Coursedata.user_id==us.id) & (Coursedata.course_id==course.id)).first()
	preq = Prerequisite.query.filter_by(course_id = course.id).count()
	pre = Prerequisite.query.filter_by(course_id = course.id).all()
	us_cou = Coursedata.query.filter((Coursedata.user_id == us.id) & (Coursedata.status_id == 1)).count()
	for i in range(len(pre)):
		us_cou_1 = Coursedata.query.filter((Coursedata.user_id == us.id) & (Coursedata.course_id == pre[i].preq_course_id) & (Coursedata.status_id == 2)).all()
	
	if a:
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'already enrolled'
		}), 400 
	if us_cou == 5 :
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'exceeded limitations'
		}), 400 


	if not us_cou_1 and preq != 0 :
			return jsonify({ 
			'error': 'Bad Request',
			'message': 'not meet minimum requirements'
		}), 400 
	coursedata = Coursedata(
		course_id=course.id, user_id=us.id,
		status_id=1
	)
	
	db.session.add(coursedata)
	db.session.commit()
	return 'Enrolled', 201

@app.route('/course/<id>')
def get_courseid(id):
	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'teacher':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
	print(id)
	course = Course.query.filter_by(id=id).first_or_404()

	return {
		'1_title': course.title, 
		'2_students': [{
				'student_id' : student.id,
		        'name': student.owner.name, 
				'status' : student.owneru.status
			 } for student in course.students 
			]
		}

@app.route('/courses')
def get_course():
	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'user':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
	print(id)
	courses = Users.query.filter_by(id=us.id).first_or_404()

	
	return {
		'1_student_name': courses.name, 
		'2_courses': [{
				'course_id'    : cours.ownere.id,
				'course_title' : cours.ownere.title,
				'status' : cours.owneru.status,
			 } for cours in courses.courses
			]
		}

@app.route('/searchcourse')
def get_coursesbytopic():
	data = request.get_json()
	if not 'topic' in data and not 'name' in data and not 'description' in data:
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'parameter not inserted'
		}), 400 
	
	if 'topic' in data:
		topic = Topic.query.filter(Topic.name.ilike('%' + data['topic'] + '%'))
		a = jsonify([
		{
			'1_name':cours.name, 
			'2_courses': [{
					 '1_id' : member.id,
		   			 '2_nama': member.title,
					 '3_description' : member.description
			} for member in cours.course 
			]
			} for cours in topic
	     ])
		return a

	if 'name' in data :
		course = Course.query.filter(Course.title.ilike('%' + data['name'] + '%'))
		b = jsonify([
		{
			'1_name':cours.title, 
			'2_description' : cours.description
			} for cours in course
		])
		return b
	
	if 'description' in data :
		coursea = Course.query.filter(Course.description.ilike('%' + data['description'] + '%'))
		c = jsonify([
		{
			'1_name':cours.title, 
			'2_description' :cours.description
			} for cours in coursea
		])
		return c

@app.route('/topiclist')
def get_topic():
	
	topic = Topic.query.all()
	y =[]
	for a in topic :
		x = a.course.count()
		z = a.name
		y.append({'name':z, 'total_courses': x}) 
	return jsonify([
		{    
			'Topic':y[j], 
		}for j in range (len(y))
	])

@app.route('/prerequisite/<id>')
def get_prerequisite(id):
	print(id)
	us_cou_1 = Prerequisite.query.filter_by(course_id = id).all()
	course = Course.query.filter_by(id= id).all()
	a = []
	for i in range(len(us_cou_1)):
		pre = Course.query.filter_by(id=us_cou_1[i].preq_course_id).first()
		a.append(pre)
	c = jsonify([
		{
		'1_name':cours.title, 
		'2_prerequisites': [{
			'1_course_name':a[j].title, 
			'2_course_description': a[j].description
			} for j in range(len(a))
			]
		} for cours in course
		 ])
	return c

@app.route('/cancel/<id>', methods=['DELETE'])
def pass_course(id):
	
	print(id)
	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'user':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
		
	coursedata = Coursedata.query.filter((Coursedata.course_id==id) & (Coursedata.user_id==us.id)).first_or_404()
	db.session.delete(coursedata)
	db.session.commit()
	return {
		'message': 'success'
		}, 201

@app.route('/pass/<id>', methods=['PUT'])
def pass_c(id):
	
	print(id)
	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'user':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
	coursedata = Coursedata.query.filter((Coursedata.course_id==id) & (Coursedata.user_id==us.id)).first_or_404()
	coursedata.status_id=2
	db.session.commit()
	return {
		'message': 'success'
		}, 201

@app.route('/daftar', methods=['POST'])
def create_user():
	data = request.get_json()
	if not 'name' in data or not 'role' in data or not 'passkey'  in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400
	u = Users(
			name=data['name'],
			role = data['role'],
			passkey=data['passkey'],

		)
	db.session.add(u)
	db.session.commit()
	return {
		'success': 'yes', 
	}, 201
@app.route('/daftar', methods=['POST'])
def daftar():
	data = request.get_json()
	if not 'name' in data or not 'role' in data or not 'passkey'  in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400
	u = Users(
			name=data['name'],
			role = data['role'],
			passkey=data['passkey'],

		)
	db.session.add(u)
	db.session.commit()
	return {
		'success': 'yes', 
	}, 201

@app.route('/user', methods=['PUT'])
def updateuser():
	data = request.get_json()
	if not 'name' in data or not 'role' in data or not 'passkey'  in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400
	idd = auth('name')
	us = Users.query.filter_by(name = idd).first()
	us.name = data['name']
	us.role = data['role']
	us.passkey = data['passkey']
	db.session.commit()
	return {
		'success': 'yes', 
	}, 201

@app.route('/topcourse')
def get_topcourse():
	
	a = db.engine.execute("select course.title, count(course.title) as frequency from coursedata join course on coursedata.course_id = course.id group by course.title order by frequency desc limit 5")
	b = []
	c = 0
	for i in a:
		c = c +1
		b.append({'1_Rank' : c,'2_course_name' : i[0],'3_students': i[1]})
	return jsonify(b)

@app.route('/topstudent')
def get_topstudent():
	
	a = db.engine.execute("select u.name, count(u.name) as frequency from coursedata join users u on coursedata.user_id = u.id where status_id = 2 group by u.name order by frequency desc limit 5")
	b = []
	c = 0
	for i in a:
		c = c +1
		b.append({'1_Rank' : c,'2_student_name' : i[0],'3_courses_completed': i[1]})
	return jsonify(b)