const fs = require('fs');

const content = fs.readFileSync('frontend/src/pages/GovernmentDashboard.jsx', 'utf8');
const lines = content.split('\n');

console.log('=== Checking GovernmentDashboard.jsx for theme issues ===');
lines.forEach((line, i) => {
  // Check for undefined vars like --text-main
  const varMatches = line.match(/var\((--[^)]+)\)/g);
  if (varMatches) {
    varMatches.forEach(v => {
      if (['var(--text-main)', 'var(--bg-main)', 'var(--surface-main)'].includes(v)) {
        console.log(`[L${i+1}] Undefined var: ${v} -> ${line.trim()}`);
      }
    });
  }

  // Check for hardcoded white backgrounds
  if (/backgroundColor:\s*['"](#fff(?:fff)?|white)['"]/i.test(line) || /background:\s*['"](#fff(?:fff)?|white)['"]/i.test(line)) {
    console.log(`[L${i+1}] White BG: ${line.trim()}`);
  }

  // Check for inputs without background
  if (/<input|<select|<textarea/.test(line) && !/className/.test(line) && !/background/.test(line)) {
    // might be default white input
    console.log(`[L${i+1}] Bare input/select: ${line.trim().slice(0, 80)}`);
  }
});
