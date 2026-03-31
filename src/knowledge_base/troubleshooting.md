# Technical Troubleshooting Guide

## Login & Authentication Issues

### Cannot log in
1. Confirm you are using the correct email address associated with your account.
2. Reset your password via the "Forgot Password" link.
3. Clear browser cookies and cache, then try again.
4. Disable browser extensions (ad blockers or password managers can interfere).
5. Try an incognito/private browsing window.
6. If using SSO (Single Sign-On), contact your IT administrator to verify your SSO configuration.

### 2FA code not working
1. Ensure your device clock is synced (authenticator apps are time-sensitive).
2. Use the backup codes provided during 2FA setup.
3. If locked out, contact support with your account email and photo ID for identity verification.

### Session keeps expiring
Sessions expire after 24 hours of inactivity by default. Enterprise customers can request extended session durations. Go to Settings → Security → Session Timeout to adjust.

---

## Application Performance

### Pages load slowly
1. Check your internet connection speed (minimum 5 Mbps recommended).
2. Clear browser cache: Chrome → Settings → Privacy → Clear Browsing Data.
3. Disable unused browser extensions.
4. Check status.example.com for active performance incidents.
5. Try a supported browser: Chrome 120+, Firefox 121+, Edge 120+, Safari 17+.

### Features not appearing or broken
1. Hard-refresh the page: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac).
2. Log out and log back in to refresh your session token.
3. Check if your plan includes the feature (Settings → Plan & Features).
4. Ensure your browser is up to date.
5. Report the issue with your browser version, OS, and steps to reproduce.

### Error codes reference
| Code | Meaning | Action |
|---|---|---|
| 401 | Authentication expired | Log out and log back in |
| 403 | Permission denied | Contact account owner to check your permissions |
| 404 | Resource not found | Verify the URL; the resource may have been deleted |
| 429 | Rate limit exceeded | Wait 60 seconds and retry; consider upgrading plan for higher limits |
| 500 | Server error | Check status.example.com; contact support if persistent |
| 503 | Service unavailable | Temporary maintenance; check status page |

---

## Integrations

### API not responding
1. Verify your API key is valid and has not expired (Settings → API Keys).
2. Confirm you are calling the correct endpoint (see docs.example.com/api).
3. Check that your IP is not blocked (enterprise firewall allowlist may be needed).
4. Review rate limits: Free plan = 100 req/min; Pro = 1,000 req/min; Enterprise = unlimited.

### Webhook not firing
1. Verify the webhook URL is publicly accessible (not localhost).
2. Check the webhook secret matches what is configured in Settings → Webhooks.
3. Review the webhook event log in Settings → Webhooks → Delivery History.
4. Ensure your server returns a 200 response within 10 seconds.

### Third-party integration not syncing
1. Disconnect and reconnect the integration under Settings → Integrations.
2. Verify the third-party service is not experiencing an outage.
3. Re-authorise OAuth permissions — they may have expired.
4. Check that required permissions/scopes were granted during authorisation.

---

## Mobile App

### App crashing on launch
1. Force-close the app and reopen.
2. Ensure the app is updated to the latest version.
3. Restart your device.
4. Uninstall and reinstall the app (your data is cloud-synced and will not be lost).
5. Report with your device model and OS version.

### Notifications not working
1. Check device notification permissions: Settings → Apps → [App Name] → Notifications.
2. Ensure Do Not Disturb is not blocking notifications.
3. In the app, go to Profile → Notification Settings and verify preferences.
4. Log out and log back in to refresh push notification token.

---

## Data & Exports

### Export not received
Exports are processed within 15 minutes and sent to your registered email. Check spam/junk folder. If not received after 30 minutes, retry the export or contact support.

### Data appears out of date
Data displayed in reports may be cached. Click the Refresh button or adjust the date range. Real-time data has a maximum delay of 5 minutes.
