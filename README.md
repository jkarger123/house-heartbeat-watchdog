# Heartbeat watchdog
Checks a secret gist every five minutes. Alerts after 12 minutes without a fresh heartbeat, computer failure, battery operation, unknown UPS status or camera failure. Sends a first alarm, reminders no more frequently than 30 minutes, and recovery. Configure repository secrets GIST_ID and NTFY_TOPIC. No address or channel is in this repository.

GitHub schedules can run 5–15 minutes late, sometimes longer, and are not a guaranteed paging service. Monthly commits keep the schedule active. Deduplication uses Actions cache. Cache loss can cause an extra first alarm. Delivery acceptance does not prove phone receipt.
