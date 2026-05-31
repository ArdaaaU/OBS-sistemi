from app import app, db, User, Course, Announcement, AttendanceLog, Enrollment
import unittest

class ComprehensivePanelTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            from app import create_initial_data
            create_initial_data()
            
            self.admin = User.query.filter_by(username='admin').first()
            self.academician = User.query.filter_by(username='academician1').first()
            self.student = User.query.filter_by(username='student1').first()
            self.course = Course.query.filter_by(code='MAT101').first()
            self.enrollment = Enrollment.query.filter_by(student_id=self.student.id, course_id=self.course.id).first()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_academician_panels_load(self):
        with self.client:
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(self.academician.id)
                sess['_fresh'] = True
                
            res = self.client.get('/academician/announcements')
            self.assertEqual(res.status_code, 200)
            
            res2 = self.client.get('/academician/attendance_panel')
            self.assertEqual(res2.status_code, 200)

    def test_attendance_edit_autonomous_absenteeism(self):
        with app.app_context():
            log = AttendanceLog(student_id=self.student.id, course_id=self.course.id, status='Gelmedi')
            db.session.add(log)
            # Suppose current absenteeism is 0, Gelmedi was manually logged without +3
            # We want to test edit logic
            self.enrollment.absenteeism = 3
            db.session.commit()
            log_id = log.id

        with self.client:
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(self.academician.id)
                sess['_fresh'] = True
                
            # Change to Geldi, should drop absenteeism by 3
            res = self.client.post(f'/academician/attendance/edit/{log_id}', data={'status': 'Geldi'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            
            with app.app_context():
                en = Enrollment.query.get(self.enrollment.id)
                self.assertEqual(en.absenteeism, 0)
                
            # Change to Gelmedi, should add 3
            res = self.client.post(f'/academician/attendance/edit/{log_id}', data={'status': 'Gelmedi'}, follow_redirects=True)
            with app.app_context():
                en = Enrollment.query.get(self.enrollment.id)
                self.assertEqual(en.absenteeism, 3)

if __name__ == '__main__':
    unittest.main()
