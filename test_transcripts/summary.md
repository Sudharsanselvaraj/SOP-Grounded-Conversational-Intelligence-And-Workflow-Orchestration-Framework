# Test Transcript 5 - Full Session Summary

**Scenario:** End-to-end session ending in a structured report.

Customer: What are your Filler prices?

Bloom AI: Dermal fillers start from £250.
Confidence: 98%

Customer: How do I cancel an appointment?

Bloom AI: Our cancellation policy requires a minimum of 24 hours' notice.
Confidence: 97%

Bloom AI: Before I let you go, may I ask a few quick questions?

Bloom AI: Could I ask what type of business you are with?
Customer: Individual

Bloom AI: Roughly how many people are on your team?
Customer: Just me

Bloom AI: What tools or software do you currently use?
Customer: None

Session ended.

Generating Conversation Summary...

```json
{
  "customer_intent": "Customer asked about pricing and cancellation policy",
  "questions_asked": [
    "What are your Filler prices?",
    "How do I cancel an appointment?"
  ],
  "lead_information": {
    "business_type": "Individual",
    "team_size": "Just me",
    "current_tools": "None"
  },
  "sop_gaps": [],
  "escalations": [],
  "recommended_next_action": "Follow up with the customer and offer the next best step from the SOP.",
  "conversation_status": "Completed"
}
```
