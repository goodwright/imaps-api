import jwt
import time
import os
from mixer.backend.django import mixer
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from core.models import User, Collection

class UserCreationTests(TestCase):

    def test_can_create_user(self):
        user = User.objects.create(
            username="locke", email="john@gmail.com", name="John Locke",
        )
        self.assertIsNone(user.last_login)
        self.assertEqual(str(user), "John Locke (locke)")
        self.assertEqual(user.password, "")
        self.assertLess(abs(time.time() - user.creation_time), 1)
        self.assertFalse(user.groups.count())
        self.assertFalse(user.admin_groups.count())
        self.assertFalse(user.group_invitations.count())
        self.assertFalse(user.collections.count())
        self.assertFalse(user.owned_collections.count())
        self.assertNotEqual(user.id, 1)
    

    def test_editing_user_doesnt_change_creation_time(self):
        user = mixer.blend(User, username="locke", creation_time=10000)
        user.name = "Hurley"
        user.save()
        self.assertEqual(user.creation_time, 10000)
    

    def test_user_uniqueness(self):
        user = mixer.blend(User, username="locke", email="john@gmail.com")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username="locke2", email="john@gmail.com")
        self.assertEqual(User.objects.count(), 1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username="locke", email="john2@gmail.com")
        self.assertEqual(User.objects.count(), 1)



class UserOrderingTests(TestCase):

    def test_users_ordered_by_creation_time(self):
        user1 = mixer.blend(User, id=2)
        user2 = mixer.blend(User, id=1)
        user3 = mixer.blend(User, id=3)
        self.assertEqual(list(User.objects.all()), [user1, user2, user3])



class UserImageTests(TestCase):

    def setUp(self):
        self.files_at_start = os.listdir("uploads")

    
    def tearDown(self):
        for f in os.listdir("uploads"):
            if f not in self.files_at_start:
                if os.path.exists(os.path.join("uploads", f)):
                    os.remove(os.path.join("uploads", f))


    def test_can_set_image(self):
        user = mixer.blend(User)
        self.assertEqual(user.image, "")
        user.image = SimpleUploadedFile("file.png", b"\x00\x01")
        user.save()
        self.assertTrue(user.image.name.startswith(str(user.id)))
        self.assertTrue(user.image.name.endswith("bVXNlcg.png"))


        
class UserPasswordTests(TestCase):

    def test_can_set_password(self):
        user = User.objects.create(
            username="locke", email="john@gmail.com", name="John Locke",
        )
        self.assertEqual(user.password, "")
        user.set_password("sw0rdfish123")
        self.assertNotEqual(user.password, "sw0rdfish")
        algorithm, iterations, salt, hash_ = user.password.split("$")
        self.assertGreaterEqual(int(iterations), 100000)



class UserTokenTests(TestCase):

    def test_access_jwt_creation(self):
        user = mixer.blend(User)
        token = user.make_access_jwt()
        token = jwt.decode(token, settings.SECRET_KEY)
        self.assertEqual(token["sub"], user.id)
        self.assertLessEqual(time.time() - token["iat"], 2)
        self.assertLessEqual(time.time() - token["expires"] - 900, 2)
    

    def test_refresh_jwt_creation(self):
        user = mixer.blend(User)
        token = user.make_refresh_jwt()
        token = jwt.decode(token, settings.SECRET_KEY)
        self.assertEqual(token["sub"], user.id)
        self.assertLessEqual(time.time() - token["iat"], 2)
        self.assertLessEqual(time.time() - token["expires"] - 31536000, 2)



class UserFromTokenTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)


    def test_no_token_returns_no_user(self):
        self.assertIsNone(User.from_token(None))
    

    def test_invalid_token_returns_no_user(self):
        self.assertIsNone(User.from_token("sdsfsfd"))
    

    def test_expired_token_returns_no_user(self):
        token = jwt.encode({
            "sub": self.user.id, "expires": 100, "iat": 1000000000000
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        self.assertIsNone(User.from_token(token))
    

    def test_unknown_user_token_returns_no_user(self):
        token = jwt.encode({
            "sub": 23, "expires": 1000000000000, "iat": 100
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        self.assertIsNone(User.from_token(token))
    

    def test_valid_token_returns_user(self):
        token = jwt.encode({
            "sub": self.user.id, "expires": 1000000000000, "iat": 100
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        self.assertEqual(User.from_token(token), self.user)



class UserCollectionsTests(TestCase):
    
    def test_users_can_own_collections(self):
        user = mixer.blend(User)
        collection1 = mixer.blend(Collection)
        user.owned_collections.add(collection1)
        self.assertEqual(list(user.owned_collections.all()), [collection1])
        self.assertEqual(list(user.collections.all()), [])
        self.assertEqual(collection1.owner, user)
    

    def test_users_can_have_access_to_collections(self):
        user = mixer.blend(User)
        collection1 = mixer.blend(Collection)
        user.collections.add(collection1)
        self.assertEqual(list(user.owned_collections.all()), [])
        self.assertEqual(list(user.collections.all()), [collection1])
        self.assertTrue(user.collectionuserlink_set.get(collection=collection1).can_edit)
        self.assertFalse(user.collectionuserlink_set.get(collection=collection1).can_execute)
        self.assertFalse(user.collections.filter(collectionuserlink__can_edit=False))
        self.assertFalse(user.collections.filter(collectionuserlink__can_execute=True))