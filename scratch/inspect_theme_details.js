const fs = require('fs');

function inspectDetails(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  console.log(`\n=== Detailed Findings for ${filePath} ===`);
  lines.forEach((line, i) => {
    // Check for hardcoded white background
    if (/background(?:Color)?:\s*['"](#fff(?:fff)?|white)['"]/i.test(line)) {
      console.log(`[L${i+1}] White BG: ${line.trim()}`);
    }
    // Check for border with hardcoded light color
    if (/border:\s*['"][^'"]*#(?:e2e8f0|e5e7eb|cbd5e1|d1d5db|e0e0e0|ccc|ddd)['"]/i.test(line)) {
      console.log(`[L${i+1}] Hardcoded Border: ${line.trim()}`);
    }
    // Check for card/surface styles that might not adapt to dark mode
    if (/(?:color|background):\s*['"]#(?:1e293b|334155|475569|64748b|0f172a|000|fff)['"]/i.test(line)) {
      console.log(`[L${i+1}] Hardcoded Color: ${line.trim()}`);
    }
    // Check for modal or dropdown backgrounds
    if (/modal|dropdown|popup|dialog/i.test(line) && /style=/i.test(line)) {
      console.log(`[L${i+1}] Modal/Dropdown style: ${line.trim()}`);
    }
  });
}

inspectDetails('frontend/src/pages/FarmerDashboard.jsx');
inspectDetails('frontend/src/pages/GovernmentDashboard.jsx');
