# Test Transcript 4 - Lead Qualification Flow

**Scenario:** A successful SOP answer leads into the sequential qualification flow.

Customer: What are your opening hours?

Bloom AI: We’re open Monday to Saturday from 9:00 AM to 7:00 PM. We are closed on Sundays.
Confidence: 98%

Bloom AI: Before I let you go, may I ask a few quick questions?

Bloom AI: Could I ask what type of business you are with?
Customer: I run a small aesthetics clinic.

Bloom AI: Roughly how many people are on your team?
Customer: 15

Bloom AI: What tools or software do you currently use?
Customer: We use HubSpot and Fresha.

Bloom AI: Thank you. Is there anything else I can help you with?

Expected outcome: All three lead fields captured and stored in memory.

```json
{
  "business_type": "I run a small aesthetics clinic.",
  "team_size": "15",
  "current_tools": "We use HubSpot and Fresha."
}
```
