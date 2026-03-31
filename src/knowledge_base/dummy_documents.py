"""Dummy knowledge base documents for Pinecone seeding.

Each document has:
- page_content: the text chunk to embed
- metadata: source, heading, category — used in retrieval results
"""

from langchain_core.documents import Document

DUMMY_DOCUMENTS: list[Document] = [

    # ── Billing ───────────────────────────────────────────────────────────
    Document(
        page_content=(
            "We accept Visa, MasterCard, American Express, Discover, and PayPal. "
            "Enterprise customers may also pay via wire transfer or purchase order. "
            "All transactions are processed securely using TLS encryption."
        ),
        metadata={"source": "faq.md", "heading": "Payment Methods", "category": "billing"},
    ),
    Document(
        page_content=(
            "Subscriptions are billed monthly or annually on the anniversary of your sign-up date. "
            "You will receive an invoice by email 3 days before each charge. "
            "To update your payment method, go to Settings → Billing → Payment Methods."
        ),
        metadata={"source": "faq.md", "heading": "Billing Cycle", "category": "billing"},
    ),
    Document(
        page_content=(
            "We offer a 30-day money-back guarantee for all new subscriptions. "
            "After 30 days, refunds are evaluated case-by-case. "
            "Annual plans may receive a prorated refund if requested within 60 days of purchase. "
            "Refunds are issued to the original payment method within 5–10 business days."
        ),
        metadata={"source": "policies.md", "heading": "Refund Policy", "category": "refund"},
    ),
    Document(
        page_content=(
            "To cancel your subscription, go to Settings → Billing → Subscription and click 'Cancel Plan'. "
            "Your access continues until the end of the current billing period. "
            "There are no cancellation fees."
        ),
        metadata={"source": "faq.md", "heading": "Cancel Subscription", "category": "billing"},
    ),
    Document(
        page_content=(
            "Upgrades take effect immediately and you are charged a prorated amount. "
            "Downgrades take effect at the start of your next billing cycle. "
            "You can switch plans at any time from Settings → Billing → Subscription."
        ),
        metadata={"source": "faq.md", "heading": "Plan Changes", "category": "billing"},
    ),

    # ── Account & Authentication ───────────────────────────────────────────
    Document(
        page_content=(
            "To reset your password, click 'Forgot Password' on the login page and enter your registered email. "
            "You will receive a reset link within 5 minutes. The link expires after 24 hours. "
            "If you don't receive the email, check your spam folder."
        ),
        metadata={"source": "faq.md", "heading": "Password Reset", "category": "account"},
    ),
    Document(
        page_content=(
            "Accounts are locked after 5 consecutive failed login attempts for security reasons. "
            "The lockout expires automatically after 30 minutes. "
            "Contact support to unlock your account immediately."
        ),
        metadata={"source": "faq.md", "heading": "Account Locked", "category": "account"},
    ),
    Document(
        page_content=(
            "Enable two-factor authentication (2FA) under Settings → Security → Two-Factor Authentication. "
            "We support Google Authenticator, Authy, and SMS verification. "
            "If your 2FA codes stop working, ensure your device clock is synced. "
            "Use backup codes if locked out."
        ),
        metadata={"source": "faq.md", "heading": "Two-Factor Authentication", "category": "account"},
    ),
    Document(
        page_content=(
            "If you suspect your account has been compromised, immediately change your password and enable 2FA. "
            "Go to Settings → Security → Active Sessions and log out of all sessions. "
            "Email support urgently — we can lock your account as a precaution and investigate."
        ),
        metadata={"source": "faq.md", "heading": "Account Compromised", "category": "account"},
    ),

    # ── Orders & Shipping ─────────────────────────────────────────────────
    Document(
        page_content=(
            "Standard shipping takes 5–7 business days. "
            "Express shipping takes 2–3 business days. "
            "Overnight shipping arrives next business day (orders must be placed before 2 PM local time). "
            "International orders take 10–21 business days depending on destination."
        ),
        metadata={"source": "faq.md", "heading": "Shipping Times", "category": "orders"},
    ),
    Document(
        page_content=(
            "Once your order ships, you will receive a tracking email with a carrier link. "
            "You can also track orders by logging in and navigating to Orders → Order History."
        ),
        metadata={"source": "faq.md", "heading": "Order Tracking", "category": "orders"},
    ),
    Document(
        page_content=(
            "If your order shows as delivered but has not arrived, wait 24 hours as packages are sometimes marked early. "
            "If still missing after 24 hours, contact support and we will file a carrier claim and reship or refund you."
        ),
        metadata={"source": "faq.md", "heading": "Missing Order", "category": "orders"},
    ),
    Document(
        page_content=(
            "Orders can be modified or cancelled within 1 hour of placement. "
            "After that, orders enter our fulfilment process and cannot be changed. "
            "Contact support immediately if you need to make changes to a recent order."
        ),
        metadata={"source": "faq.md", "heading": "Order Cancellation", "category": "orders"},
    ),

    # ── Technical Support ─────────────────────────────────────────────────
    Document(
        page_content=(
            "If the application is slow or not loading: "
            "1. Clear your browser cache and cookies. "
            "2. Try a different browser. "
            "3. Disable browser extensions. "
            "4. Check status.example.com for known outages. "
            "Supported browsers: Chrome 120+, Firefox 121+, Edge 120+, Safari 17+."
        ),
        metadata={"source": "troubleshooting.md", "heading": "Application Performance", "category": "tech_support"},
    ),
    Document(
        page_content=(
            "Common HTTP error codes: "
            "401 = Authentication expired — log out and log back in. "
            "403 = Permission denied — check your account permissions. "
            "429 = Rate limit exceeded — wait 60 seconds and retry. "
            "500 = Server error — check status.example.com. "
            "503 = Service unavailable — temporary maintenance."
        ),
        metadata={"source": "troubleshooting.md", "heading": "Error Codes", "category": "tech_support"},
    ),
    Document(
        page_content=(
            "API rate limits: Free plan = 100 requests/min, Pro = 1,000 requests/min, Enterprise = unlimited. "
            "If you receive a 429 error, wait 60 seconds and retry. "
            "Verify your API key is active under Settings → API Keys."
        ),
        metadata={"source": "troubleshooting.md", "heading": "API Rate Limits", "category": "tech_support"},
    ),
    Document(
        page_content=(
            "To export your data: go to Settings → Data → Export. "
            "Select the date range and format (CSV or JSON) and click Export. "
            "You will receive a download link by email within 15 minutes. "
            "If not received after 30 minutes, check spam or retry the export."
        ),
        metadata={"source": "faq.md", "heading": "Data Export", "category": "tech_support"},
    ),

    # ── Privacy & Compliance ──────────────────────────────────────────────
    Document(
        page_content=(
            "All data is encrypted at rest (AES-256) and in transit (TLS 1.3). "
            "We are SOC 2 Type II certified and GDPR compliant. "
            "Data is hosted in AWS data centres in the US and EU."
        ),
        metadata={"source": "faq.md", "heading": "Data Security", "category": "privacy"},
    ),
    Document(
        page_content=(
            "GDPR subject access requests must be fulfilled within 30 days. "
            "GDPR deletion requests must be completed within 30 days. "
            "To delete your account, go to Settings → Account → Delete Account "
            "or email support with the subject 'Account Deletion Request'."
        ),
        metadata={"source": "policies.md", "heading": "GDPR & Data Rights", "category": "privacy"},
    ),

    # ── SLA & Compensation ────────────────────────────────────────────────
    Document(
        page_content=(
            "Support SLA response times: "
            "Urgent: 1 hour first response, 4 hour resolution. "
            "High: 4 hour first response, 1 business day resolution. "
            "Medium: 8 hour first response, 3 business day resolution. "
            "Low: 24 hour first response, 7 business day resolution. "
            "Business hours: Monday–Friday 9 AM–6 PM UTC. Urgent tickets handled 24/7."
        ),
        metadata={"source": "policies.md", "heading": "Service Level Agreement", "category": "billing"},
    ),
    Document(
        page_content=(
            "Compensation guidelines: "
            "Service outage > 4 hours: 1 week credit. "
            "Service outage > 24 hours: 1 month credit. "
            "Billing error (overcharge): full refund + 10% credit. "
            "Missed SLA on High/Urgent ticket: 1 week credit. "
            "Data loss due to our fault: full refund of affected period."
        ),
        metadata={"source": "policies.md", "heading": "Compensation Guidelines", "category": "billing"},
    ),
]
