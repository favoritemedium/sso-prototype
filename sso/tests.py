from django.test import TestCase
from .models import VerifyEmail
from faker import Faker

# Create randomized test data.
# See http://fake-factory.readthedocs.org/en/latest/ for details.
fake = Faker()

class VerifyEmailTestCase(TestCase):

    def test_create(self):
        email = fake.email()
        token = VerifyEmail.generate_token(email)
        self.assertEqual(len(token), 64)
        email1 = VerifyEmail.redeem_token(token)
        self.assertEqual(email, email1)

    def test_not_found(self):
        email = fake.email()
        token = VerifyEmail.generate_token(email)
        email1 = VerifyEmail.redeem_token('adifferenttoken')
        self.assertIsNone(email1)

    def test_find_correct_email(self):
        email1 = fake.email()
        email2 = fake.email()
        token1 = VerifyEmail.generate_token(email1)
        token2 = VerifyEmail.generate_token(email2)
        email3 = VerifyEmail.redeem_token(token2)
        email4 = VerifyEmail.redeem_token(token1)
        self.assertEqual(email1, email4)
        self.assertEqual(email2, email3)

    def test_expired(self):
        email = fake.email()
        token = VerifyEmail.generate_token(email)

        # set the timestamp back a day
        ve = VerifyEmail.objects.first()
        ve.expires -= 86401
        ve.save()

        email1 = VerifyEmail.redeem_token(token)
        self.assertIsNone(email1)

    def test_grace_period(self):
        email = fake.email()
        token = VerifyEmail.generate_token(email)

        # set the timestamp back almost a day
        ve = VerifyEmail.objects.first()
        ve.expires -= 86390
        ve.save()

        email1 = VerifyEmail.redeem_token(token)
        self.assertEqual(email, email1)

        # set the timestamp back another 9 minutes
        ve = VerifyEmail.objects.first()
        ve.expires -= 540
        ve.save()

        # should still be good, even though it's more than a day old now
        email2 = VerifyEmail.redeem_token(token)
        self.assertEqual(email, email2)

    def test_remove(self):
        email1 = fake.email()
        email2 = fake.email()
        token1 = VerifyEmail.generate_token(email1)
        token2 = VerifyEmail.generate_token(email2)
        self.assertEqual(VerifyEmail.objects.count(), 2)

        VerifyEmail.remove(email1)
        self.assertEqual(VerifyEmail.objects.count(), 1)

        email3 = VerifyEmail.redeem_token(token2)
        email4 = VerifyEmail.redeem_token(token1)
        self.assertEqual(email2, email3)
        self.assertIsNone(email4)

    def test_cron(self):
        email1 = fake.email()
        email2 = fake.email()
        token1 = VerifyEmail.generate_token(email1)
        token2 = VerifyEmail.generate_token(email2)
        self.assertEqual(VerifyEmail.objects.count(), 2)

        ve = VerifyEmail.objects.first()
        ve.expires -= 86401
        ve.save()

        VerifyEmail.cron()
        self.assertEqual(VerifyEmail.objects.count(), 1)

        email3 = VerifyEmail.redeem_token(token2)
        email4 = VerifyEmail.redeem_token(token1)
        self.assertEqual(email2, email3)
        self.assertIsNone(email4)


