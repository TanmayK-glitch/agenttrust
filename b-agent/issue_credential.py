from datetime import datetime, timedelta, timezone
import os

import jwt
from dotenv import load_dotenv


load_dotenv()


def issue_credential() -> str:
	secret = os.getenv("AGENTTRUST_SECRET")
	if not secret:
		raise RuntimeError("AGENTTRUST_SECRET is missing from the environment")

	expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
	payload = {
		"agent_id": "shopper-1",
		"scopes": ["read_inbox", "make_payment"],
		"max_amount": 500,
		"exp": expires_at,
	}

	return jwt.encode(payload, secret, algorithm="HS256")


if __name__ == "__main__":
	print(issue_credential())
