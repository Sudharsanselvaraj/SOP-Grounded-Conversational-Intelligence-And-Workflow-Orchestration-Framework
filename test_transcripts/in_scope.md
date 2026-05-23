# Test Transcript 1 - In-SOP Question

**Scenario:** The customer asks about Botox pricing and a free consultation.

Customer: What are your Botox prices?

Bloom AI: Botox treatments start from £200.
Confidence: 98%

Customer: Do you offer free consultations?

Bloom AI: Yes. We offer a free consultation.
Confidence: 97%

Expected outcome: SOP-backed answer returned, no escalation, source_found=true.

```json
{
  "answer": "Botox treatments start from £200.",
  "confidence": 0.98,
  "source_found": true,
  "requires_escalation": false
}
```
