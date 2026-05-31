from app import app, db, User, Course, Enrollment, AttendanceLog
import unittest

class AttendanceTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Create users
            academician = User(username='academician1', password_hash='hash', role='academician', name='Test Hoca')
            student = User(username='student1', password_hash='hash', role='student', name='Test Ogrenci')
            db.session.add_all([academician, student])
            db.session.commit()
            
            self.academician_id = academician.id
            self.student_id = student.id
            
            # Create course and enrollment
            course = Course(name='Test Ders', code='TST101', academician_id=academician.id)
            db.session.add(course)
            db.session.commit()
            self.course_id = course.id
            
            enrollment = Enrollment(student_id=student.id, course_id=course.id, absenteeism=0)
            db.session.add(enrollment)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_take_attendance(self):
        with self.client:
            # Login as academician directly via session
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(self.academician_id)
                sess['_fresh'] = True
            
            # Post attendance
            response = self.client.post(f'/take_attendance/{self.course_id}', data={
                f'attendance_{self.student_id}': 'Gelmedi'
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Yoklama', response.data)
            
            # Check DB
            with app.app_context():
                log = AttendanceLog.query.first()
                self.assertIsNotNone(log)
                self.assertEqual(log.status, 'Gelmedi')
                
                enrollment = Enrollment.query.first()
                self.assertEqual(enrollment.absenteeism, 3)

if __name__ == '__main__':
    unittest.main()
