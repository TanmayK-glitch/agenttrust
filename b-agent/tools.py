import jwt
import os
from dotenv import load_dotenv

load_dotenv()

def fake_gateway(token, tool, args):
    print(f"[Gateway] Checking permission for: {tool}")

    secret = os.getenv("AGENTTRUST_SECRET")

    try:
        credential = jwt.decode(
            token,
            secret,
            algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        return {
            "decision": "BLOCK",
            "reason": "Invalid credential",
        }

    allowed_scopes = credential.get("scopes", [])
    max_amount = credential.get("max_amount", 0)

    if tool not in allowed_scopes:
        return {
            "decision": "BLOCK",
            "reason": f"Tool '{tool}' is not permitted",
        }

    if tool == "make_payment":
        amount = args.get("amount", 0)

        if amount > max_amount:
            return {
                "decision": "BLOCK",
                "reason": f"Payment exceeds limit of ₹{max_amount}",
            }

    return {
        "decision": "ALLOW",
        "reason": "Credential and policy checks passed",
    }


def read_inbox(token):
    result = fake_gateway(token, "read_inbox", {})

    if result["decision"] != "ALLOW":
        print("[BLOCKED] read_inbox")
        return

    print("[TOOL] Reading inbox...")
    print("[INBOX] You have 2 new emails.")


def send_email(to, subject, body, token):
    result = fake_gateway(
        token,
        "send_email",
        {
            "to": to,
            "subject": subject,
            "body": body,
        },
    )

    if result["decision"] != "ALLOW":
        print("[BLOCKED] send_email")
        return

    print("[TOOL] Sending email...")
    print(f"[EMAIL] To: {to}")
    print(f"[EMAIL] Subject: {subject}")
    print(f"[EMAIL] Body: {body}")


def make_payment(amount, recipient, token):
    result = fake_gateway(
        token,
        "make_payment",
        {
            "amount": amount,
            "recipient": recipient,
        },
    )

    if result["decision"] != "ALLOW":
        print("[BLOCKED] make_payment")
        return

    print("[TOOL] Making payment...")
    print(f"[PAYMENT] ₹{amount} → {recipient}")


if __name__ == "__main__":
    token = input("Paste JWT: ")

    read_inbox(token)

    send_email(
        "alice@example.com",
        "Hello",
        "This is a test email.",
        token
    )

    make_payment(
        500,
        "merchant-1",
        token
    )