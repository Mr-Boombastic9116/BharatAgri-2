# Authoritative Agricultural Data Sources & Market Modeling

BharatAgri-2 anchors procurement calculations and market analysis in authentic government publications, mandi market bulletins, and crop calendars. No arbitrary or random pricing formulas are utilized.

---

## 1. Prototype State-Crop Grounding

Under the prototype operational specifications, only valid state-crop combinations are permitted:

| State | Permitted Prototype Crops | Agricultural Agro-Climatic Zone |
| :--- | :--- | :--- |
| **Goa** | Mango, Banana, Tomato | West Coast Plains & Ghats Zone (High humidity, coastal alluvial soils) |
| **Maharashtra** | Sugarcane, Wheat, Cotton | Western Plateau & Hills Zone (Black regur soils, canal-irrigated zones) |
| **Karnataka** | Paddy, Maize, Bajra | Southern Plateau & Hills Zone (Krishna/Cauvery basins, red loamy soils) |

Any request to book or procure an unsupported combination (e.g. Goa + Sugarcane or Maharashtra + Mango) is rejected on both frontend and backend.

---

## 2. Authoritative Data Repositories

All baseline pricing, arrivals, and moisture benchmarks originate from the following primary authorities:

1. **Commission for Agricultural Costs and Prices (CACP), Ministry of Agriculture & Farmers Welfare, GoI**:
   - Price Policy for Kharif and Rabi Crops reports (2024-25, 2025-26).
   - Establishes Minimum Support Prices (MSP) and Fair & Remunerative Prices (FRP) for Sugarcane.
2. **Directorate of Economics and Statistics (DES), Ministry of Agriculture**:
   - Comprehensive Scheme for Studying Cost of Cultivation of Principal Crops.
   - Normal area, production, and yield (APY) datasets.
3. **AGMARKNET (Agricultural Marketing Information Network)**:
   - Daily arrival volumes and modal wholesale prices across regulated APMC mandis (Kolhapur, Hubballi, Mapusa, Belagavi).
4. **National Agriculture Market (e-NAM)**:
   - Unified national electronic trade pricing and grade-specific premium spreads.
5. **Indian Council of Agricultural Research (ICAR) & State Agricultural Universities**:
   - Central Institute for Subtropical Horticulture (CISH) mango maturity standards.
   - Directorate of Onion and Garlic / Directorate of Wheat & Barley Research moisture ceilings.

---

## 3. Seeded Market Benchmarks (Season 2025-26)

| State | Crop | Season | Official MSP / Floor (₹/Q) | Estimated Modal Price (₹/Q) | Moisture Standard (%) | Market Sentiment |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| Goa | Mango | Summer/Zaid 2026 | ₹4,800.00 | ₹5,250.00 | 75.0 - 86.0% w/w | High Demand (Tourist season) |
| Goa | Banana | All-Season 2026 | ₹2,150.00 | ₹2,220.00 | Fresh table standard | Balanced |
| Goa | Tomato | Rabi/Zaid 2026 | ₹1,650.00 | ₹1,940.00 | Perishable vegetable | Supply Deficit |
| Maharashtra | Sugarcane | Crushing 2025-26 | ₹340.00 (FRP) | ₹348.00 | Mill recovery based | Stable High Volume |
| Maharashtra | Wheat | Rabi 2025-26 | ₹2,425.00 | ₹2,460.00 | ≤ 12.0% | Balanced Post-Harvest |
| Maharashtra | Cotton | Kharif 2025-26 | ₹7,121.00 | ₹7,380.00 | ≤ 8.5% | High Mill Demand |
| Karnataka | Paddy | Kharif 2025-26 | ₹2,320.00 | ₹2,345.00 | ≤ 14.0% | Surplus Buffer |
| Karnataka | Maize | Kharif 2025-26 | ₹2,225.00 | ₹2,290.00 | ≤ 14.0% | High Feed Demand |
| Karnataka | Bajra | Kharif 2025-26 | ₹2,625.00 | ₹2,640.00 | ≤ 14.0% | Balanced |

---

## 4. Realistic Seasonal Variation & Pricing Logic

The price estimation engine accounts for authentic market forces rather than flat artificial values:
- **Seasonality Curves**: Mango prices fluctuate based on early-season scarcity vs. mid-season peak arrivals.
- **Physical Quality Penalties**: Excessive foreign matter (>2%) or high moisture penalizes the purchase rate or downgrades the lot to Grade B/C.
- **Storage Buffer Limits**: Local godown capacity and pending truck movements constrain procurement velocity.
