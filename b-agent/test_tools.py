import os
import unittest
from datetime import datetime, timedelta, timezone

import jwt

from tools import fake_gateway


SECRET = "test-agenttrust-secret-with-32-bytes"


def make_token(**claims):
    payload = {
        "scopes": ["make_payment"],
        "max_amount": 500,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    payload.update(claims)
    return jwt.encode(payload, SECRET, algorithm="HS256")


class GatewayPaymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_secret = os.environ.get("AGENTTRUST_SECRET")
        os.environ["AGENTTRUST_SECRET"] = SECRET

    @classmethod
    def tearDownClass(cls):
        if cls.previous_secret is None:
            os.environ.pop("AGENTTRUST_SECRET", None)
        else:
            os.environ["AGENTTRUST_SECRET"] = cls.previous_secret

    def check_decision(self, amount, expected):
        result = fake_gateway(
            make_token(),
            "make_payment",
            {"amount": amount, "recipient": "merchant"},
        )
        self.assertEqual(result["decision"], expected)

    def test_payment_amount_policy(self):
        cases = [
            (500, "ALLOW"),
            (1, "ALLOW"),
            (0, "BLOCK"),
            (-5000, "BLOCK"),
            ("500", "BLOCK"),
            (True, "BLOCK"),
            (None, "BLOCK"),
            (501, "BLOCK"),
            (10000, "BLOCK"),
        ]

        for amount, expected in cases:
            with self.subTest(amount=amount):
                self.check_decision(amount, expected)

    def test_missing_payment_arguments_block(self):
        result = fake_gateway(make_token(), "make_payment", {})
        self.assertEqual(result["decision"], "BLOCK")

    def test_malformed_payment_arguments_block(self):
        result = fake_gateway(make_token(), "make_payment", None)
        self.assertEqual(result["decision"], "BLOCK")

    def test_missing_expiry_blocks(self):
        token = make_token()
        claims = jwt.decode(token, SECRET, algorithms=["HS256"])
        claims.pop("exp")
        token_without_exp = jwt.encode(claims, SECRET, algorithm="HS256")

        result = fake_gateway(
            token_without_exp,
            "make_payment",
            {"amount": 1, "recipient": "merchant"},
        )
        self.assertEqual(result["decision"], "BLOCK")

    def test_malformed_credential_claims_block(self):
        for claims in ({"scopes": "make_payment"}, {"max_amount": "500"}):
            with self.subTest(claims=claims):
                result = fake_gateway(
                    make_token(**claims),
                    "make_payment",
                    {"amount": 1, "recipient": "merchant"},
                )
                self.assertEqual(result["decision"], "BLOCK")

    def test_invalid_token_blocks_without_crashing(self):
        result = fake_gateway(
            "not-a-jwt",
            "make_payment",
            {"amount": 1, "recipient": "merchant"},
        )
        self.assertEqual(result["decision"], "BLOCK")


if __name__ == "__main__":
    unittest.main()