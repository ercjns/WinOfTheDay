
import os
from os.path import abspath, dirname, join
import wotdapp
import unittest
import tempfile

_cwd = dirname(abspath(__file__))

class WotdTestHelpers(unittest.TestCase):

    def setUp(self):
        wotdapp.app.config['TESTING'] = True
        wotdapp.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + join(_cwd, 'automatedtesting.db')
        wotdapp.app.config['REQUIRE_CAPTCHA'] = False
        self.app = wotdapp.app.test_client()
        with wotdapp.app.app_context():
            wotdapp.db.create_all()

    def tearDown(self):
        with wotdapp.app.app_context():
            wotdapp.db.session.remove()
            wotdapp.db.drop_all()

    def register(self, username, password):
        return self.app.post('/join', data=dict(
            username=username,
            pw1=password,
            pw2=password
        ), follow_redirects=True)

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            pw=password
        ), follow_redirects=True)

    def register_and_login(self, username, password):
        self.register(username, password)
        return self.login(username, password)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def submit(self, content):
        return self.app.post('/submit', data=dict(
            content=content
        ), follow_redirects=True)

class WotdTests(WotdTestHelpers):

    def test_empty_posts_db(self):
        rv = self.app.get('/')
        assert 'populate this when something goes wrong' in rv.data

    def test_register(self):
        rv = self.register('testrunner', 'testrunnerpw')
        assert 'You can try logging in now' in rv.data
        rv = self.register('testrunner', 'testrunnerpw')
        assert 'That username already exists' in rv.data

    def test_login_logout(self):
        rv = self.register_and_login('testrunner', 'testrunnerpw')
        assert "Logged in." in rv.data
        rv = self.logout()
        assert "You have logged out" in rv.data
        rv = self.login('testXrunnerX', 'testrunnerpw')
        assert "Hmm, I do not recognize that username" in rv.data
        rv = self.login('testrunner', 'testXrunnerXpwX')
        assert "Hmm, that password is not correct" in rv.data

    def test_user_page_noauth(self):
        rv = self.app.get('/me', follow_redirects=True)
        assert 'need to login to access that page' in rv.data

    def test_user_page(self):
        self.register_and_login('testrunner', 'testrunnerpw')
        rv = self.app.get('/me')
        assert 'Submit today' in rv.data
        assert 'testrunner' in rv.data

    def test_submit_page(self):
        rv = self.app.get('/submit')
        assert 'Celebrate' in rv.data

    def test_anon_submit(self):
        rv = self.submit('anonymous test post')
        assert 'Keep up the good work' in rv.data
        assert 'anonymous test post' in rv.data
        with wotdapp.app.app_context():
            p = wotdapp.models.Post.query.first()
            assert p.content == 'anonymous test post'
            assert p.user_id == None
            assert p.isApproved == None

    def test_user_submit(self):
        self.register_and_login('testrunner', 'testrunnerpw')
        rv = self.submit('test post with user context')
        assert 'Keep up the good work' in rv.data
        assert 'test post with user context' in rv.data
        with wotdapp.app.app_context():
            u = wotdapp.models.User.query.first()
            p = wotdapp.models.Post.query.first()
            assert p.content == 'test post with user context'
            assert p.user_id == u.id
            assert p.isApproved == None
        rv = self.app.get('/me')
        assert 'Look at all this goodness' in rv.data
        assert 'test post with user context' in rv.data
        self.logout()

    def test_user_settings(self):
        self.register_and_login('testrunner', 'testrunnerpw')
        rv = self.app.post('/me', data=dict(
            email="wotdtester@example.com",
            displayname="Test Runner"
        ), follow_redirects=True)
        assert 'Settings Updated' in rv.data
        assert 'Hey Test Runner' in rv.data
        assert 'wotdtester@example.com' in rv.data



class WotdModTests(WotdTestHelpers):

    def make_mod(self, username):
        with wotdapp.app.app_context():
            u = wotdapp.models.User.query.filter_by(username=username).one()
            u.isMod = True
            wotdapp.db.session.add(u)
            wotdapp.db.session.commit()

    def test_mod_page_noauth(self):
        rv = self.app.get('/mod', follow_redirects=True)
        assert 'need to login to access that page' in rv.data
        rv = self.app.get('/mod/post', follow_redirects=True)
        assert 'need to login to access that page' in rv.data

    def test_mod_page_badauth(self):
        self.register_and_login('testrunner', 'testrunnerpw')
        rv = self.app.get('/mod')
        assert '403' in rv.status
        rv = self.app.get('/mod/post')
        assert '403' in rv.status
        self.logout()

    def test_mod_page(self):
        self.register_and_login('testrunneradmin', 'testrunneradminpw')
        self.make_mod('testrunneradmin')
        rv = self.app.get('/mod')
        assert 'Moderation Home' in rv.data
        self.logout()

    def test_mod_posts(self):
        self.register_and_login('testrunneradmin', 'testrunneradminpw')
        self.make_mod('testrunneradmin')
        rv = self.app.get('/mod/post')
        assert 'Moderate Post' in rv.data
        self.logout()


if __name__ == '__main__':
    unittest.main()