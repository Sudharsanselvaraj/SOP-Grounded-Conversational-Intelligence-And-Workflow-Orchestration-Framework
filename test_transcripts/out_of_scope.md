# Test Transcript 2 - Out-of-Scope Question

**Scenario:** The customer asks for information not present in the SOP.

Customer: What Botox brand do you use?

Bloom AI: I’m sorry, I don’t have that information in the current SOP, so I can’t confirm it reliably. I’ll connect you with a member of our team who can help.
Confidence: 15%

Escalation logged: SOP gap

Expected outcome: No hallucination, escalation triggered, source_found=false.

```json
{
  "answer": "I’m sorry, I don’t have that information in the current SOP, so I can’t confirm it reliably. I’ll connect you with a member of our team who can help.",
  "confidence": 0.15,
  "source_found": false,
  "requires_escalation": true
}
```
