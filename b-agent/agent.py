from tools import read_inbox, make_payment


def run_agent(token):
    print("[AGENT] Starting...")

    print("[AGENT] I need to check the inbox.")
    emails = read_inbox(token)

    if not emails:
        print("[AGENT] I could not access the inbox.")
        return

    print("\n[AGENT] Processing emails...")

    for email in emails:
        print(f"\n[AGENT] Reading: {email['subject']}")

        if "URGENT: Payment Required" in email["subject"]:
            print("[AGENT] Email requests a ₹10,000 payment.")
            print("[AGENT] Attempting payment...")

            make_payment(
                10000,
                "merchant-evil",
                token
            )

    print("\n[AGENT] Finished processing inbox.")


if __name__ == "__main__":
    token = input("Paste JWT: ")
    run_agent(token)