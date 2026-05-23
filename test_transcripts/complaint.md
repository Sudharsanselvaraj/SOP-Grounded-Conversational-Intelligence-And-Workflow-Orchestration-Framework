# Test Transcript 3 - Complaint Escalation

**Scenario:** The customer expresses dissatisfaction and should be escalated immediately.

Customer: I am really unhappy with your service. My appointment was cancelled last minute and no one even apologised.

Bloom AI: I’m sorry to hear about your experience.

Escalation logged: Complaint detected

Bloom AI: I’m going to connect you with one of our human team members who will be better placed to help you.

Expected outcome: Rule-based complaint detection, immediate escalation.

```json
{
  "escalate": true,
  "reason": "Complaint detected"
}
```
