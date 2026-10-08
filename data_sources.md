# Authoritative Agricultural Data Sources & Metadata

This document catalogs all official external agricultural data sources used in the **BharatAgri-2** procurement intelligence platform, satisfying the data lineage and provenance requirements.

---

## 1. Statutory State & Crop Combinations (Prototype Specification)

| State | Designated Crops | Agro-Climatic Zone | Primary Mandi / APMC Hubs |
| :--- | :--- | :--- | :--- |
| **Goa** | **Mango**, **Banana**, **Tomato** | Western Coastal Plains & Ghats Zone | Sanquelim, Mapusa, Margao, Ponda, Valpoi |
| **Maharashtra** | **Sugarcane**, **Wheat**, **Cotton** | Western Maharashtra / Vidarbha / Marathwada | Baramati, Kolhapur (Karvir/Shirol), Nashik (Niphad), Nagpur (Katol/Saoner) |
| **Karnataka** | **Paddy**, **Maize**, **Bajra** | Northern Dry Zone & Southern Transition Zone | Chikkodi, Gokak, Athani, Hubballi-Amargol, Kundgol |

---

## 2. External Data Source Registry

### Source 1: Commission for Agricultural Costs and Prices (CACP)
* **Agency / Publisher**: Commission for Agricultural Costs and Prices, Ministry of Agriculture & Farmers Welfare, Government of India.
* **Official URL**: https://cacp.dac.gov.in/
* **Report / Release**: Price Policy for Kharif Crops (2024-25, 2025-26) and Price Policy for Rabi Crops (2024-25, 2025-26).
* **Retrieval Date**: October 2026.
* **Data Fields Retained**:
  - `official_msp_per_quintal`: Minimum Support Price / Fair & Remunerative Price (FRP for Sugarcane).
  - Statutory benchmark rates for FAQ (Fair Average Quality) produce.
* **Transformation / Curation**:
  - Direct statutory values adopted without artificial distortion.
  - Paddy (Grade A): Rs 2,320 / quintal.
  - Maize: Rs 2,225 / quintal.
  - Bajra: Rs 2,625 / quintal.
  - Wheat: Rs 2,425 / quintal.
  - Cotton (Medium Staple): Rs 7,121 / quintal.
  - Sugarcane (Statutory FRP): Rs 340 / quintal (benchmarked at 10.25% basic sugar recovery rate).

### Source 2: Directorate of Economics and Statistics (DES)
* **Agency / Publisher**: Department of Agriculture and Farmers Welfare, Govt of India.
* **Official URL**: https://desagri.gov.in/
* **Report / Release**: Agricultural Statistics at a Glance & First Advance Estimates of Production of Foodgrains and Commercial Crops.
* **Retrieval Date**: October 2026.
* **Data Fields Retained**:
  - State-level production estimates (`expected_supply_quintals`).
  - Net sown area, seasonal sowing/harvesting calendars.
* **Transformation / Curation**:
  - Normalized to quintals (1 Quintal = 100 kg) across all state-crop pairs.
  - Applied realistic intra-state district allocations representing local mandi catchments.

### Source 3: AGMARKNET (Agricultural Marketing Information Network) & e-NAM
* **Agency / Publisher**: Directorate of Marketing & Inspection (DMI), Ministry of Agriculture and Farmers Welfare, Govt of India.
* **Official URL**: https://agmarknet.gov.in/ | https://enam.gov.in/
* **Report / Release**: Daily Mandi Arrivals and Modal Price Time Series for Major Markets (Goa GSAMB, Maharashtra MSAMB, Karnataka KSAMB).
* **Retrieval Date**: October 2026.
* **Data Fields Retained**:
  - Modal prices (`estimated_procurement_price`), daily arrival velocities, market sentiments.
  - Historical price variance and seasonal price elasticity.
* **Transformation / Curation**:
  - Preserved authentic market price deviations driven by seasonal demand/supply imbalances rather than static formulas.
  - High demand in Goa for tourist-season fruits (Mango & Banana) reflects realistic local wholesale premiums over base floor rates.

### Source 4: ICAR - Central Coastal Agricultural Research Institute (CCARI), Goa
* **Agency / Publisher**: Indian Council of Agricultural Research, Old Goa.
* **Official URL**: https://ccari.icar.gov.in/
* **Report / Release**: Technical Bulletin on Post-Harvest Handling, Maturity Standards, and Quality Grading of Mankurad Mango & Moira Banana.
* **Retrieval Date**: October 2026.
* **Data Fields Retained**:
  - Specific gravity, skin color chromaticity transitions, Fair Average Quality criteria, shelf-life characteristics.
* **Transformation / Curation**:
  - Informed the prototype grading criteria (Visual Grade + Moisture Content + Foreign Matter thresholds).

---

## 3. Separation of Agricultural Data from ML Training Datasets

> **Strict Architectural Boundary**:
> The Mango AI disease classification datasets (`MangoDHDS`, `MangoFruitBD`, `MangoFruitDDs`) are **strictly isolated** from operational agricultural and procurement databases. The image datasets are used exclusively for computer vision quality inspection and are **never** mixed with mandi price, booking, farmer registration, or state supply-demand statistics.
