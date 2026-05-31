from app import app, db, User, Course, Announcement
import unittest

class NewFeaturesTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            from app import create_initial_data
            create_initial_data()
            
            # The app.py already seeded users during import, so we query them
            self.admin = User.query.filter_by(username='admin').first()
            self.academician = User.query.filter_by(username='academician1').first()
            
            self.admin_id = self.admin.id
            self.academician_id = self.academician.id
            
            self.course = Course.query.filter_by(code='TEST101').first()
            if not self.course:
                self.course = Course(name='Test Ders', code='TEST101', academician_id=self.academician.id)
                db.session.add(self.course)
                db.session.commit()
            self.course_id = self.course.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_edit_user(self):
        with self.client:
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(self.admin_id)
                sess['_fresh'] = True
            
            response = self.client.post(f'/admin/edit_user/{self.academician_id}', data={
                'username': 'ac_new',
                'name': 'Ac New',
                'role': 'academician',
                'password': ''
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            with app.app_context():
                user = User.query.get(self.academician_id)
                self.assertEqual(user.username, 'ac_new')
                self.assertEqual(user.name, 'Ac New')

    def test_add_announcement(self):
        with self.client:
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(self.academician_id)
                sess['_fresh'] = True
                
            response = self.client.post('/academician/add_announcement', data={
                'course_id': str(self.course_id),
                'title': 'Test Duyuru',
                'content': 'Duyuru Icerigi'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            with app.app_context():
                ann = Announcement.query.first()
                self.assertIsNotNone(ann)
                self.assertEqual(ann.title, 'Test Duyuru')

if __name__ == '__main__':
    unittest.main()
