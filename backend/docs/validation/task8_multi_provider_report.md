# Task 8 — Real Multi-Provider Structured-Output Validation

This is a single-run snapshot of provider behavior at the time this script ran. It is not a guarantee of future provider behavior, and carries no pass/fail threshold — purely observational, per approved Sprint 2 Task 8 scope.

## anthropic: 3/6 conformed

### Non-conforming responses

**Input:** What information do you need before designing a conveyor system?

**Raw response:**
```
{
  "clarifying_questions": [
    "What material(s) will be conveyed (bulk solids, unit loads, packages, pallets, liquids-in-containers), and what are their sizes, weights, and shapes?",
    "What is the required throughput or capacity (e.g., tons/hour, units/minute)?",
    "What is the total conveying distance and elevation change, and is the path straight, inclined, curved, or multi-directional?",
    "What is the operating environment (indoor/outdoor, temperature, humidity, dust, corrosive atmosphere, washdown requirements, hazardous zone classification)?",
    "What are the load characteristics (abrasiveness, temperature, moisture content, fragility, stackability)?",
    "What is the desired duty cycle and operating hours per day (continuous vs. intermittent)?",
    "Are there specific speed or takt-time requirements dictated by upstream/downstream equipment?",
    "What are the interface points — infeed/discharge heights, existing equipment, or automation systems (PLC, sensors, sorters)?",
    "What are the space/layout constraints (footprint, ceiling height, floor loading capacity)?",
    "Are there regulatory, safety, or industry-specific standards to comply with (OSHA, FDA, ATEX, CE)?",
    "What is the budget range and expected payback/ROI timeframe?",
    "Is noise level or energy consumption a critical constraint?",
    "What level of automation/control integration is required (variable speed, sorting, accumulation, diverting)?",
    "What is the expected lifespan and maintenance accessibility requirement?"
  ],
  "engineering_reasoning": "Conveyor system design is highly application-dependent, since the choice of conveyor type (belt, roller, chain, screw, pneumatic, vibratory, overhead), drive sizing, structural design, and controls all stem from the material properties, throughput, layout, and environment. Without these inputs, any preliminary sizing (motor power, belt width, speed) would be speculative. The reasoning approach is first to characterize the load and process requirements (what, how much, how far, how fast), then the environmental and interface constraints (where and how it connects to the rest of the line), and finally the operational and compliance constraints (safety, automation, maintenance). This staged information gathering allows for right-sizing components (motor, belt/chain, supports) and selecting a conveyor type suited to the material and layout before detailed calculations (power requirements, belt tension, roller spacing, structural loading) can be performed with confidence.",
  "preliminary_calculations": {
    "status": "Insufficient data for calculations",
    "assumed_belt_speed_mps": 1.0,
    "assumed_capacity_tph": 50,
    "note": "Placeholder values only; actual power, tension, and structural calculations require throughput, distance, incline, and material data"
  },
  "material_suggestions": [
    "Mild steel (structural frame, cost-effective)",
    "Stainless steel 304/316 (food-grade, washdown, or corrosive environ
```

**Input:** Design a steel plate carrying a 50 kN tensile load with a factor of safety of 3.

**Raw response:**
```
{
  "clarifying_questions": [
    "What is the plate's intended connection method (bolted, pinned, or welded)?",
    "Is there a preferred plate thickness or width constraint due to space or existing hardware?",
    "Will the plate have holes for fasteners, and if so, what diameter and edge distance are required?",
    "What is the operating environment (corrosive, high temperature, outdoor exposure)?",
    "Is the load static or does it include cyclic/fatigue components?",
    "What steel grade is preferred or already stocked (e.g., A36, A572, stainless)?"
  ],
  "engineering_reasoning": "The plate is sized as a simple tension member. Required cross-sectional area is determined from the allowable stress, which is the material yield strength divided by the specified factor of safety (FoS = 3). A36 mild steel (yield ~250 MPa) was assumed as a common, cost-effective structural material. The allowable stress becomes yield/FoS = 83.3 MPa. Required area = Load / Allowable stress = 50,000 N / 83.3 MPa = 600 mm². A practical thickness (10 mm) was chosen based on typical plate stock availability, giving the required width. If the plate will have a bolt hole, the net section (gross width minus hole diameter times thickness) must be re-checked against the same allowable stress, so hole size and connection type are critical missing inputs. No fatigue or buckling check was performed since load type (static vs. cyclic) and support conditions were not specified.",
  "preliminary_calculations": {
    "tensile_load_kn": 50,
    "factor_of_safety": 3,
    "assumed_material": "A36 mild steel",
    "yield_strength_mpa": 250,
    "allowable_stress_mpa": 83.3,
    "required_area_mm2": 600,
    "assumed_thickness_mm": 10,
    "calculated_width_mm": 60,
    "recommended_width_with_margin_mm": 70,
    "note_on_holes": "If bolted, net area (width - hole_dia) x thickness must still meet 600 mm^2 minimum"
  },
  "material_suggestions": [
    "ASTM A36 mild steel (economical, widely available)",
    "ASTM A572 Grade 50 high-strength low-alloy steel (if weight reduction is needed)",
    "Stainless steel 304/316 (if cor
```

**Input:** I need a shaft to transmit 10 kW at 500 rpm and I need recommendations for both material selection and manufacturing methods.

**Raw response:**
```
{
  "clarifying_questions": [
    "What is the duty cycle (continuous, intermittent, or shock-loaded)?",
    "Is the shaft subjected to bending loads in addition to torsion (e.g., overhung pulley or gear)?",
    "What type of end connections are required (keyway, spline, coupling, flange)?",
    "What is the operating environment (temperature, corrosive media, presence of lubrication)?",
    "Are there space or weight constraints limiting shaft diameter or length?",
    "What is the required design life or fatigue consideration (reversing loads, cyclic operation)?"
  ],
  "engineering_reasoning": "The torque was derived from the given power and rotational speed using T = P / omega, where omega = 2*pi*N/60. A service factor was applied to account for typical minor shock loading and bending effects common in general-purpose power transmission shafts. The shaft diameter was then sized using the standard torsional shear stress equation d = (16*T_design / (pi * tau_allow))^(1/3), assuming a conservative allowable shear stress for a medium-carbon steel with a keyway stress concentration factor included. This provides a baseline diameter; a full fatigue and deflection check should follow once loading details (bending, cyclic nature) are confirmed.",
  "preliminary_calculations": {
    "power_kw": 10,
    "speed_rpm": 500,
    "angular_velocity_rad_s": 52.36,
    "torque_nm": 191,
    "service_factor": 1.5,
    "design_torque_nm": 286.5,
    "allowable_shear_stress_mpa": 42,
    "calculated_shaft_diameter_mm": 32.5,
    "recommended_standard_diameter_mm": 35
  },
  "material_suggestions": [
    "AISI 1045 medium-carbon steel (good strength-to-cost ratio, widely available, machinable)",
    "AISI 4140 alloy steel (higher fatigue strength if shock loading or reversing torque is present)",
    "AISI 4340 alloy steel (for high-performance or high-load applications requiring superior toughness)",
    "Stain
```

### Qualitative notes
_(fill in manually after reviewing the raw fixtures above — documented only, no fix proposed under Task 8)_

## openai: 0/6 conformed

### Non-conforming responses

**Input:** I need a shaft to transmit 5 kW at 300 rpm.

**Error:** OpenAI API returned an error: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-proj-*******************************************************************************************************************Tc4t. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401}

**Input:** I need a bracket for a machine.

**Error:** OpenAI API returned an error: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-proj-*******************************************************************************************************************Tc4t. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401}

**Input:** How many letters are in the word ENGINEERAI?

**Error:** OpenAI API returned an error: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-proj-*******************************************************************************************************************Tc4t. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401}

**Input:** What information do you need before designing a conveyor system?

**Error:** OpenAI API returned an error: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-proj-*******************************************************************************************************************Tc4t. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401}

**Input:** Design a steel plate carrying a 50 kN tensile load with a factor of safety of 3.

**Error:** OpenAI API returned an error: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-proj-*******************************************************************************************************************Tc4t. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401}

**Input:** I need a shaft to transmit 10 kW at 500 rpm and I need recommendations for both material selection and manufacturing methods.

**Error:** OpenAI API returned an error: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-proj-*******************************************************************************************************************Tc4t. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401}

### Qualitative notes
_(fill in manually after reviewing the raw fixtures above — documented only, no fix proposed under Task 8)_
