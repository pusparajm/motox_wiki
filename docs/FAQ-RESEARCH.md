# Motorcycle FAQ research

Research date: 2026-11-21

## Sites reviewed

Model pages were reviewed across sport, commuter, scooter, adventure, cruiser and electric bikes.

- BikeDekho
- BikeWale
- Zigwheels
- Carandbike
- Bikez (specification structure)
- MCN (used-bike ownership content)
- Motorcycle.com (review/specification pages)
- Cycle-ergo (rider-fit reference)

## FAQ patterns found

### Market and purchase questions

These appear on most Indian price-led sites:

- On-road price, ex-showroom price
- EMI and down payment
- Current offers
- Variants and colour options
- Dealer availability
- Launch date

These are useful for a price-comparison site, but not for a global, market-neutral reference database. MotoX Wiki does not store local pricing, finance or dealer data, so these were not added.

### Specification questions

Common and suitable for our data:

- Engine displacement
- Power and torque
- Top speed (only where verified)
- Kerb weight
- Seat height
- Fuel-tank capacity
- Tyres and wheel type
- ABS or combined braking
- Suspension front and rear
- Brakes front and rear
- Transmission and final drive
- Dimensions, wheelbase and ground clearance

### Ownership and service questions

Suitable where we hold the data:

- Service interval
- Engine-oil capacity and grade
- Fork-oil grade, quantity or air gap
- Fork seal, dust seal and slide-bush sizes
- Rear shock type
- Beginner-shortlist fit, using the site's power, weight, seat-height and category rules
- European A2 power and power-to-weight limits
- Seat-height band for shorter-rider context
- Brake fluid and coolant
- Common reliability or used-buying checks

### Rider-fit and use questions

Useful but often editorial rather than purely factual:

- Is it suitable for beginners?
- Is it A2-legal?
- Is it comfortable for shorter riders?
- Is it good for city use, touring, pillion use or off-road use?
- Does it vibrate or produce heat in traffic?
- Is the riding posture aggressive or upright?

These need either measured data or a clearly stated editorial basis. MotoX Wiki can answer beginner and A2 questions from power, weight and seat height, but should avoid blanket claims about comfort, heat or reliability without a source.

### Electric-specific questions

- Range
- Battery capacity
- Charging time and fast-charging support
- Top speed
- Licence requirement
- Battery warranty

These are valuable, but our current catalogue does not hold enough verified electric drivetrain data for most models.

## What was added

The model-page FAQ generator now produces data-backed answers for:

- Power and torque
- Engine displacement
- Top speed where listed
- Seat height
- Kerb weight
- Calculated power-to-weight ratio
- Fuel capacity
- Tyres
- ABS or combined braking
- Front and rear suspension
- Front and rear brakes
- Service interval
- Engine oil capacity and grade
- Fork oil data
- Fork seal size
- Rear shock type
- Beginner-shortlist fit, using the site's power, weight, seat-height and category rules
- European A2 power and power-to-weight limits
- Seat-height band for shorter-rider context

The generator only emits a question when the underlying field exists and is not a placeholder value.

## What was deliberately left out

- Prices, EMI, offers, colours and dealer data: market-specific and not stored in the catalogue.
- Mileage and fuel economy: not verified across enough models.
- Comfort, heat, vibration and reliability: requires editorial testing or a cited owner survey.
- Generic “which is better” questions: handled by dedicated comparison pages instead.
- Launch dates and future-model questions: not a stable specification reference.

## Similar sites

- **Zigwheels** — model pages with price, specifications, FAQ schema and comparison links.
- **Carandbike** — long-form model FAQs covering performance, ergonomics, features and ownership.
- **Bikez** — deep specification catalogue with dimensions, model history and comparison tools.
- **MCN** — road tests and used-buying guides with reliability and ownership notes.
- **Motorcycle.com** — reviews, specifications and model comparisons.
- **Autoevolution** — model histories and technical specification pages.
- **Cycle-ergo** — seat-height and rider-fit reference.
- **MotoSpecVault** — model-year specification source already used by the catalogue.
