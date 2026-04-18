## Payment Model Decision

We considered:
1. Only payment steps
2. Only schedule rows
3. Both

Final Decision:
Keep both:
- payment_steps → pattern
- lease_payment_schedules → operational rows

Reason:
- Need flexibility for editing
- Need efficiency for recurring payments
- Asset removal affects row-level schedule