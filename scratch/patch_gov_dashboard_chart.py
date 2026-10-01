with open('frontend/src/pages/GovernmentDashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add supplyDemandChartMode state if not present
if 'supplyDemandChartMode' not in content:
    old_state = "const [priceEstimateResult, setPriceEstimateResult] = useState(null);"
    new_state = """const [priceEstimateResult, setPriceEstimateResult] = useState(null);
  const [supplyDemandChartMode, setSupplyDemandChartMode] = useState('volume'); // 'volume' | 'price'"""
    content = content.replace(old_state, new_state, 1)

# 2. Add the Recharts graph and custom tooltip right before <div style={{ overflowX: 'auto' }}>
old_table_section = """            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>"""

chart_and_table_code = """            {/* Chart / Visualization Mode Toggle & Recharts Graph (Requirement 9) */}
            {supplyDemand.length > 0 && (
              <div style={{ marginBottom: '1.5rem', background: 'var(--bg-page)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--secondary)' }}>
                    Comparative Market Intelligence ({selectedState !== 'Nationwide' ? selectedState : 'Nationwide'})
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      type="button"
                      className={`btn ${supplyDemandChartMode === 'volume' ? 'btn-primary' : 'btn-outline'}`}
                      style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
                      onClick={() => setSupplyDemandChartMode('volume')}
                    >
                      Supply vs Demand vs Storage (Q)
                    </button>
                    <button
                      type="button"
                      className={`btn ${supplyDemandChartMode === 'price' ? 'btn-primary' : 'btn-outline'}`}
                      style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
                      onClick={() => setSupplyDemandChartMode('price')}
                    >
                      Official MSP vs Estimated Price (₹/Q)
                    </button>
                  </div>
                </div>

                <div style={{ width: '100%', height: 260 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    {supplyDemandChartMode === 'volume' ? (
                      <BarChart
                        data={supplyDemand.map(d => ({
                          ...d,
                          name: selectedState === 'Nationwide' ? `${d.state}: ${d.crop}` : d.crop
                        }))}
                        margin={{ top: 10, right: 15, left: 10, bottom: 25 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.6} />
                        <XAxis dataKey="name" stroke="var(--muted)" fontSize={11} interval={0} angle={-15} textAnchor="end" />
                        <YAxis stroke="var(--muted)" fontSize={11} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (!active || !payload || !payload.length) return null;
                            const d = payload[0].payload;
                            return (
                              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.78rem', boxShadow: 'var(--shadow-md)', color: 'var(--secondary)' }}>
                                <div style={{ fontWeight: 800, color: 'var(--primary)', marginBottom: '4px' }}>{d.state} — {d.crop}</div>
                                <div>Expected Supply: <strong>{Number(d.expected_supply_quintals).toLocaleString()} Q</strong></div>
                                <div>Current Procurement: <strong>{Number(d.current_procurement_quintals).toLocaleString()} Q</strong></div>
                                <div>Projected Procurement: <strong>{Number(d.projected_procurement_quintals).toLocaleString()} Q</strong></div>
                                <div>Expected Demand: <strong>{Number(d.expected_demand_quintals).toLocaleString()} Q</strong></div>
                                <div>Available Storage: <strong>{Number(d.available_storage_quintals).toLocaleString()} Q</strong></div>
                                <div style={{ marginTop: '4px', borderTop: '1px solid var(--border)', paddingTop: '4px' }}>
                                  Surplus / Deficit: <strong style={{ color: d.surplus_deficit_quintals >= 0 ? 'var(--success-text)' : 'var(--danger-text)' }}>
                                    {d.surplus_deficit_quintals >= 0 ? '+' : ''}{Number(d.surplus_deficit_quintals).toLocaleString()} Q ({d.supply_status})
                                  </strong>
                                </div>
                                <div style={{ color: 'var(--muted)', fontSize: '0.72rem', marginTop: '2px' }}>Official MSP: ₹{Number(d.official_msp).toLocaleString()}/Q • Est Price: ₹{Number(d.estimated_procurement_price).toLocaleString()}/Q</div>
                              </div>
                            );
                          }}
                        />
                        <Legend wrapperStyle={{ fontSize: '0.75rem', paddingTop: '6px' }} />
                        <Bar dataKey="expected_supply_quintals" name="Expected Supply" fill="#0284c7" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="expected_demand_quintals" name="Expected Demand" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="current_procurement_quintals" name="Current Procurement" fill="#16a34a" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="available_storage_quintals" name="Available Storage" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    ) : (
                      <BarChart
                        data={supplyDemand.map(d => ({
                          ...d,
                          name: selectedState === 'Nationwide' ? `${d.state}: ${d.crop}` : d.crop
                        }))}
                        margin={{ top: 10, right: 15, left: 10, bottom: 25 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.6} />
                        <XAxis dataKey="name" stroke="var(--muted)" fontSize={11} interval={0} angle={-15} textAnchor="end" />
                        <YAxis stroke="var(--muted)" fontSize={11} tickFormatter={(v) => `₹${v}`} />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (!active || !payload || !payload.length) return null;
                            const d = payload[0].payload;
                            return (
                              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.78rem', boxShadow: 'var(--shadow-md)', color: 'var(--secondary)' }}>
                                <div style={{ fontWeight: 800, color: 'var(--primary)', marginBottom: '4px' }}>{d.state} — {d.crop}</div>
                                <div>Official MSP: <strong>₹ {Number(d.official_msp).toLocaleString()} / Q</strong></div>
                                <div>Estimated State Procurement Price: <strong style={{ color: '#8b5cf6' }}>₹ {Number(d.estimated_procurement_price).toLocaleString()} / Q</strong></div>
                                <div style={{ marginTop: '4px', borderTop: '1px solid var(--border)', paddingTop: '4px' }}>
                                  Price Spread: <strong>₹ {(Number(d.estimated_procurement_price) - Number(d.official_msp)).toFixed(2)} / Q</strong>
                                </div>
                                <div style={{ color: 'var(--muted)', fontSize: '0.72rem', marginTop: '2px' }}>Supply Status: {d.supply_status} • Storage Avail: {Number(d.available_storage_quintals).toLocaleString()} Q</div>
                              </div>
                            );
                          }}
                        />
                        <Legend wrapperStyle={{ fontSize: '0.75rem', paddingTop: '6px' }} />
                        <Bar dataKey="official_msp" name="Official MSP (₹/Q)" fill="#16a34a" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="estimated_procurement_price" name="Estimated State Procurement Price (₹/Q)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    )}
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>"""

content = content.replace(old_table_section, chart_and_table_code, 1)

with open('frontend/src/pages/GovernmentDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Government Dashboard graph patch applied successfully!")
