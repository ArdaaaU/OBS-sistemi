from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Course, Enrollment, AttendanceLog, Announcement
import os
import csv
from io import StringIO
from flask import Response
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'obs-secret-key-1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///obs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_initial_data():
    hashed_password = generate_password_hash('123456', method='pbkdf2:sha256')
    
    # Admin
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password_hash=hashed_password, role='admin', name='Sistem Yöneticisi'))
        
    # Students
    students_data = [('student1', 'Ali Yılmaz'), ('student2', 'Ayşe Demir'), ('student3', 'Mehmet Kaya')]
    for uname, name in students_data:
        if not User.query.filter_by(username=uname).first():
            db.session.add(User(username=uname, password_hash=hashed_password, role='student', name=name))
            
    # Academicians
    acads_data = [('academician1', 'Dr. Ahmet Hoca'), ('academician2', 'Prof. Dr. Elif Hoca')]
    for uname, name in acads_data:
        if not User.query.filter_by(username=uname).first():
            db.session.add(User(username=uname, password_hash=hashed_password, role='academician', name=name))
            
    db.session.commit()
    
    # Courses
    ac1 = User.query.filter_by(username='academician1').first()
    ac2 = User.query.filter_by(username='academician2').first()
    
    courses_data = [
        ('MAT101', 'Matematik', ac1.id if ac1 else None, 15),
        ('Fiz101', 'Fizik', ac2.id if ac2 else None, 20),
        ('KIM101', 'Kimya', ac1.id if ac1 else None, 10)
    ]
    for code, name, ac_id, max_abs in courses_data:
        if not Course.query.filter_by(code=code).first():
            db.session.add(Course(name=name, code=code, academician_id=ac_id, max_absenteeism=max_abs))
            
    db.session.commit()
    
    # Enroll students
    s1 = User.query.filter_by(username='student1').first()
    s2 = User.query.filter_by(username='student2').first()
    s3 = User.query.filter_by(username='student3').first()
    
    c1 = Course.query.filter_by(code='MAT101').first()
    c2 = Course.query.filter_by(code='Fiz101').first()
    c3 = Course.query.filter_by(code='KIM101').first()
    
    enrollments_data = [(s1, c1), (s1, c2), (s2, c1), (s3, c3)]
    for student, course in enrollments_data:
        if student and course:
            if not Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first():
                db.session.add(Enrollment(student_id=student.id, course_id=course.id))
                
    db.session.commit()

with app.app_context():
    db.create_all()
    create_initial_data()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'academician':
            return redirect(url_for('academician_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'academician':
                return redirect(url_for('academician_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- ADMIN ROUTES ---
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Yetkisiz Erişim", 403
    users = User.query.all()
    courses = Course.query.all()
    academicians = User.query.filter_by(role='academician').all()
    students = User.query.filter_by(role='student').all()
    return render_template('admin_dashboard.html', users=users, courses=courses, academicians=academicians, students=students)

@app.route('/admin_users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return "Yetkisiz Erişim", 403
    users = User.query.all()
    academicians = User.query.filter_by(role='academician').all()
    return render_template('admin_users.html', users=users, academicians=academicians)

@app.route('/admin_assignments')
@login_required
def admin_assignments():
    if current_user.role != 'admin':
        return "Yetkisiz Erişim", 403
    students = User.query.filter_by(role='student').all()
    courses = Course.query.all()
    return render_template('admin_assignments.html', students=students, courses=courses)

@app.route('/admin/user/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return "Yetkisiz Erişim", 403
    username = request.form.get('username')
    name = request.form.get('name')
    role = request.form.get('role')
    
    if User.query.filter_by(username=username).first():
        flash('Bu kullanıcı adı zaten mevcut.', 'danger')
        return redirect(url_for('admin_users'))
        
    hashed_password = generate_password_hash('123456', method='pbkdf2:sha256')
    new_user = User(username=username, name=name, role=role, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    flash(f'{role.capitalize()} {name} başarıyla eklendi. Şifre: 123456', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return "Yetkisiz Erişim", 403
    user = User.query.get_or_404(user_id)
    
    username = request.form.get('username')
    name = request.form.get('name')
    role = request.form.get('role')
    password = request.form.get('password')
    
    # Check if new username exists
    if username != user.username and User.query.filter_by(username=username).first():
        flash('Bu kullanıcı adı zaten mevcut.', 'danger')
        return redirect(url_for('admin_users'))
        
    user.username = username
    user.name = name
    user.role = role
    
    if password:
        user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    db.session.commit()
    flash('Kullanıcı başarıyla güncellendi.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return "Yetkisiz Erişim", 403
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Kendinizi silemezsiniz.', 'danger')
        return redirect(url_for('admin_users'))
        
    if user.role == 'student':
        Enrollment.query.filter_by(student_id=user.id).delete()
    elif user.role == 'academician':
        courses = Course.query.filter_by(academician_id=user.id).all()
        for c in courses:
            c.academician_id = None
            
    db.session.delete(user)
    db.session.commit()
    flash('Kullanıcı silindi.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/course/add', methods=['POST'])
@login_required
def add_course():
    if current_user.role != 'admin':
        return "Yetkisiz Erişim", 403
    name = request.form.get('name')
    code = request.form.get('code')
    academician_id = request.form.get('academician_id')
    max_absenteeism = request.form.get('max_absenteeism', type=int)
    
    if Course.query.filter_by(code=code).first():
        flash('Bu ders kodu zaten mevcut.', 'danger')
        return redirect(url_for('admin_users'))
        
    try:
        academician_id = int(academician_id) if academician_id else None
        max_abs = max_absenteeism if max_absenteeism is not None else 20
        new_course = Course(name=name, code=code, academician_id=academician_id, max_absenteeism=max_abs)
        db.session.add(new_course)
        db.session.commit()
        flash('Ders başarıyla eklendi.', 'success')
    except Exception as e:
        flash('Hata: ID Tipi Uyuşmazlığı.', 'danger')
        
    return redirect(url_for('admin_users'))

@app.route('/admin/enroll', methods=['POST'])
@login_required
def enroll_student():
    if current_user.role != 'admin':
        return "Yetkisiz Erişim", 403
    student_id = int(request.form.get('student_id'))
    course_id = int(request.form.get('course_id'))
    
    existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if existing:
        flash('Öğrenci zaten bu derse kayıtlı.', 'danger')
    else:
        enrollment = Enrollment(student_id=student_id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash('Öğrenci derse kaydedildi.', 'success')
    return redirect(url_for('admin_assignments'))

# --- ACADEMICIAN ROUTES ---
@app.route('/academician_dashboard')
@login_required
def academician_dashboard():
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    # Sorumlu olduğu dersleri çek
    courses = Course.query.filter_by(academician_id=current_user.id).all()
    return render_template('academician_dashboard.html', courses=courses)

@app.route('/academician/add_announcement', methods=['POST'])
@login_required
def add_announcement():
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    course_id = request.form.get('course_id')
    title = request.form.get('title')
    content = request.form.get('content')
    
    course = Course.query.get_or_404(int(course_id))
    if course.academician_id != current_user.id:
        return "Yetkisiz Erişim", 403
        
    ann = Announcement(title=title, content=content, course_id=course.id, academician_id=current_user.id)
    db.session.add(ann)
    db.session.commit()
    flash('Duyuru başarıyla paylaşıldı.', 'success')
    return redirect(url_for('academician_dashboard'))

@app.route('/academician/announcements')
@login_required
def academician_announcements():
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    announcements = Announcement.query.filter_by(academician_id=current_user.id).order_by(Announcement.date.desc()).all()
    return render_template('academician_announcements.html', announcements=announcements)

@app.route('/academician/announcement/delete/<int:id>', methods=['POST'])
@login_required
def delete_announcement(id):
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    ann = Announcement.query.get_or_404(id)
    if ann.academician_id != current_user.id:
        return "Yetkisiz Erişim", 403
    db.session.delete(ann)
    db.session.commit()
    flash('Duyuru başarıyla silindi.', 'success')
    return redirect(url_for('academician_announcements'))

@app.route('/academician/announcement/edit/<int:id>', methods=['POST'])
@login_required
def edit_announcement(id):
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    ann = Announcement.query.get_or_404(id)
    if ann.academician_id != current_user.id:
        return "Yetkisiz Erişim", 403
    title = request.form.get('title')
    content = request.form.get('content')
    if title and content:
        ann.title = title
        ann.content = content
        db.session.commit()
        flash('Duyuru başarıyla güncellendi.', 'success')
    return redirect(url_for('academician_announcements'))

@app.route('/academician/attendance_panel')
@login_required
def academician_attendance():
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    
    courses = Course.query.filter_by(academician_id=current_user.id).all()
    course_ids = [c.id for c in courses]
    
    # Tüm yoklama kayıtlarını çek, tarihe göre sırala
    logs = AttendanceLog.query.filter(AttendanceLog.course_id.in_(course_ids)).order_by(AttendanceLog.date.desc()).all()
    
    return render_template('academician_attendance.html', courses=courses, logs=logs)

@app.route('/academician/attendance/edit/<int:log_id>', methods=['POST'])
@login_required
def edit_attendance(log_id):
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
        
    log = AttendanceLog.query.get_or_404(log_id)
    if log.course.academician_id != current_user.id:
        return "Yetkisiz Erişim", 403
        
    new_status = request.form.get('status')
    if new_status and new_status != log.status:
        enrollment = Enrollment.query.filter_by(student_id=log.student_id, course_id=log.course_id).first()
        if enrollment:
            if log.status == 'Gelmedi' and new_status == 'Geldi':
                enrollment.absenteeism = max(0, enrollment.absenteeism - 3)
            elif log.status == 'Geldi' and new_status == 'Gelmedi':
                enrollment.absenteeism += 3
                
        log.status = new_status
        db.session.commit()
        flash('Yoklama kaydı güncellendi.', 'success')
        
    return redirect(url_for('academician_attendance'))

@app.route('/academician/export_report/<int:course_id>')
@login_required
def export_report(course_id):
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    course = Course.query.get_or_404(course_id)
    if course.academician_id != current_user.id:
        return "Yetkisiz Erişim", 403
        
    enrollments = Enrollment.query.filter_by(course_id=course.id).all()
    
    output = StringIO()
    # Add BOM for Excel utf-8 recognition
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Ogrenci No', 'Ad Soyad', 'Vize', 'Final', 'Proje', 'Sunum', 'Devamsizlik'])
    
    for en in enrollments:
        writer.writerow([
            en.student.username,
            en.student.name,
            en.midterm_grade if en.midterm_grade is not None else '',
            en.final_grade if en.final_grade is not None else '',
            en.project_grade if en.project_grade is not None else '',
            en.presentation_grade if en.presentation_grade is not None else '',
            en.absenteeism
        ])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={course.code}_Not_Raporu.csv"}
    )

@app.route('/academician_course/<int:course_id>')
@login_required
def academician_course(course_id):
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    course = Course.query.get_or_404(course_id)
    if course.academician_id != current_user.id:
        return "Bu derse erişim yetkiniz yok.", 403
    # Derse ait tüm öğrenci kayıtlarını (Enrollment) çek
    enrollments = Enrollment.query.filter_by(course_id=course.id).all()
    return render_template('academician_course.html', course=course, enrollments=enrollments)

@app.route('/take_attendance/<int:course_id>', methods=['POST'])
@login_required
def take_attendance(course_id):
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    course = Course.query.get_or_404(course_id)
    if course.academician_id != current_user.id:
        return "Bu derse erişim yetkiniz yok.", 403
    
    enrollments = Enrollment.query.filter_by(course_id=course.id).all()
    date_now = datetime.utcnow()
    
    for enrollment in enrollments:
        status = request.form.get(f'attendance_{enrollment.student_id}')
        if status in ['Geldi', 'Gelmedi']:
            log = AttendanceLog(student_id=enrollment.student_id, course_id=course.id, date=date_now, status=status)
            db.session.add(log)
            if status == 'Gelmedi':
                enrollment.absenteeism += 3
                
    db.session.commit()
    flash('Yoklama başarıyla kaydedildi.', 'success')
    return redirect(url_for('academician_course', course_id=course.id))

@app.route('/update_grade/<int:enrollment_id>', methods=['POST'])
@login_required
def update_grade(enrollment_id):
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    if enrollment.course.academician_id != current_user.id:
        return "Yetkisiz Erişim", 403
        
    midterm = request.form.get('midterm')
    final = request.form.get('final')
    project = request.form.get('project')
    presentation = request.form.get('presentation')
    absenteeism = request.form.get('absenteeism')
    
    enrollment.midterm_grade = float(midterm) if midterm else None
    enrollment.final_grade = float(final) if final else None
    enrollment.project_grade = float(project) if project else None
    enrollment.presentation_grade = float(presentation) if presentation else None
    enrollment.absenteeism = int(absenteeism) if absenteeism else 0
    
    db.session.commit()
    flash('Notlar ve devamsızlık güncellendi.', 'success')
    return redirect(url_for('academician_course', course_id=enrollment.course_id))

@app.route('/student_detail/<int:student_id>')
@login_required
def student_detail(student_id):
    if current_user.role != 'academician':
        return "Yetkisiz Erişim", 403
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return "Bu kullanıcı bir öğrenci değil.", 400
    # Öğrencinin tüm kayıtlarını çek
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    return render_template('student_detail.html', student=student, enrollments=enrollments)

# --- STUDENT ROUTES ---
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return "Yetkisiz Erişim", 403
    # Öğrencinin tüm kayıtlarını çek
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    
    # Her enrollment için yoklama geçmişini (logs) çekip objeye ekleyelim
    for enrollment in enrollments:
        enrollment.logs = AttendanceLog.query.filter_by(student_id=current_user.id, course_id=enrollment.course_id).order_by(AttendanceLog.date.desc()).all()
        
    return render_template('student_dashboard.html', enrollments=enrollments)

if __name__ == '__main__':
    app.run(debug=True)
