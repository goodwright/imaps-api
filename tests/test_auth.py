import kirjava
import base64
import requests
import jwt
import json
import time
from django.conf import settings
from .base import FunctionalTest
from core.models import User

class SignupTests(FunctionalTest):

    def test_can_signup(self):
        users_at_start = User.objects.count()

        # Create user
        result = self.client.execute("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rdfish123",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""")

        # There's a new user
        self.assertEqual(User.objects.count(), users_at_start + 1)
        new_user = User.objects.last()
        self.assertEqual(new_user.username, "kate")
        self.assertEqual(new_user.email, "kate@gmail.com")
        self.assertEqual(new_user.name, "Kate Austen")
        self.assertNotEqual(new_user.password, "sw0rdfish123")
        self.assertLess(time.time() - new_user.last_login, 10)

        # An access token has been returned
        access_token = result["data"]["signup"]["accessToken"]
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], new_user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 900, 10)

        # A HTTP-only cookie has been set with the refresh token
        refresh_token = self.client.session.cookies["refresh_token"]
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], new_user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 31536000, 10)
    

    def test_signup_validation(self):
        users_at_start = User.objects.count()

        # Name must be short enough
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rdfish123",
            username: "kate",
            name: "000001111122222333334444455555666667777788888999990"
        ) { accessToken } }""", message="50 characters")
        self.assertEqual(User.objects.count(), users_at_start)

        # Email must be unique
        self.check_query_error("""mutation { signup(
            email: "jack@gmail.com", password: "sw0rdfish123",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""", message="already exists")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)

        # Username must be unique
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rdfish123",
            username: "jack", name: "Kate Austen"
        ) { accessToken } }""", message="already exists")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)

        # Password must be 9 or more characters
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rd123",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""", message="too short")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)

        # Password can't be numeric
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "238442378572385238",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""", message="numeric")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)

        # Password must be reasonably uncommon
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "password123",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""", message="too common")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)



class LoginTests(FunctionalTest):

    def test_can_login(self):
        # Send credentials
        result = self.client.execute("""mutation { login(
            username: "jack", password: "livetogetha",
        ) { accessToken } }""")

        # An access token has been returned
        access_token = result["data"]["login"]["accessToken"]
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], self.user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 900, 10)

        # A HTTP-only cookie has been set with the refresh token
        refresh_token = self.client.session.cookies["refresh_token"]
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], self.user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 31536000, 10)

        # Last login has been updated
        self.user.refresh_from_db()
        self.assertLess(time.time() - self.user.last_login, 10)
    

    def test_login_can_fail(self):
        # Incorrect username
        self.check_query_error("""mutation { login(
            username: "claire", password: "livetogetha"
        ) { accessToken} }""", message="Invalid credentials")
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.last_login)

        # Incorrect password
        self.check_query_error("""mutation { login(
            username: "jack", password: "wrongpassword"
        ) { accessToken} }""", message="Invalid credentials")
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.last_login)



class TokenRefreshTests(FunctionalTest):

    def test_can_refresh_token(self):
        # Send mutation with cookie
        original_refresh_token = self.user.make_refresh_jwt()
        cookie_obj = requests.cookies.create_cookie(
            domain="localhost.local", name="refresh_token",
            value=original_refresh_token
        )
        self.client.session.cookies.set_cookie(cookie_obj)
        result = self.client.execute("mutation { refreshToken { accessToken } }")

        # An access token has been returned
        access_token = result["data"]["refreshToken"]["accessToken"]
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], self.user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 900, 10)

        # A new HTTP-only cookie has been set with the refresh token
        refresh_token = self.client.session.cookies["refresh_token"]
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], self.user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 31536000, 10)
    

    def test_token_refresh_can_fail(self):
        # No cookies
        self.check_query_error(
            "mutation { refreshToken { accessToken } }", message="No refresh token"
        )
        self.assertFalse("refresh_token" in self.client.session.cookies)

        # Refresh token garbled
        cookie_obj = requests.cookies.create_cookie(
            domain="localhost.local", name="refresh_token", value="sadafasdf"
        )
        self.client.session.cookies.set_cookie(cookie_obj)
        self.check_query_error(
            "mutation { refreshToken { accessToken } }", message="Refresh token not valid"
        )
        
        # Refresh token expired
        token = jwt.encode({
            "sub": self.user.id, "iat": 1000000000000, "expires": 2000
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        cookie_obj = requests.cookies.create_cookie(
            domain="localhost.local", name="refresh_token", value=token
        )
        self.client.session.cookies.set_cookie(cookie_obj)
        self.check_query_error(
            "mutation { refreshToken { accessToken } }", message="Refresh token not valid"
        )