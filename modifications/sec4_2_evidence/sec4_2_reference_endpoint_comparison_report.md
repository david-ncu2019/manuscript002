# Section 4.2 Reference Endpoint Comparison

## Comparison design

This audit compares cumulative endpoint errors on identical calendar intervals. The reference sums the monthly estimates from the delayed-delivery analysis, whereas the reduced-frequency scenario updates the model from one cumulative field measurement at each endpoint. Endpoint error is estimated accumulated deformation minus observed accumulated deformation.

The 12-month Section 4.1 reference combines two six-month prediction cycles and includes one model recalibration at the midpoint; it is not an immediate monthly-update reference.

## Horizon accumulation

Within the Section 4.1 reference, pooled endpoint MAE increased from 1.430 mm over six months to 2.431 mm over twelve months. The difference of 1.001 mm describes error accumulation across a longer interval and should not be attributed to reduced field measurements.

## Additional reduced-frequency difference

At six months, pooled endpoint MAE was 1.430 mm for the reference and 1.468 mm under reduced-frequency updating. The paired MAE difference was 0.039 mm, with a 95% bootstrap interval from -0.038 to 0.115 mm. The interval included zero.

At twelve months, pooled endpoint MAE was 2.431 mm for the reference and 2.462 mm under reduced-frequency updating. The paired MAE difference was 0.031 mm, with a 95% bootstrap interval from -0.115 to 0.169 mm. The interval included zero.

## Differences among depth sections

- 6-month endpoints: higher MAE in S2, S5, S6; lower MAE in S1, S3, S4.
- 12-month endpoints: higher MAE in S2, S3, S5; lower MAE in S1, S4, S6.

The mixed directions show that the pooled difference does not describe every depth section equally. Section-level values and intervals should therefore remain available when the pooled result is discussed.

## Manuscript wording boundary

Safe wording should separate the error accumulated over a longer endpoint interval from the additional difference associated with reduced field measurements. The paired bootstrap interval should accompany any statement about that additional difference. Avoid claims of statistical sameness, zero performance loss, interval optimality, or sufficiency of the initial record. This comparison does not test the deferred common-origin 3-, 5-, and 8-year question.
