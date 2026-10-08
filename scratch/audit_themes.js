const fs = require('fs');

function auditFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  console.log(`\n=== Auditing ${filePath} (${content.length} bytes, ${content.split('\n').length} lines) ===`);

  // Look for inline styles with hardcoded colors
  const hardcodedWhiteBg = [...content.matchAll(/background(?:Color)?:\s*['"](#fff(?:fff)?|white)['"]/gi)];
  const hardcodedDarkBg = [...content.matchAll(/background(?:Color)?:\s*['"](#(?:000|0f172a|1e293b|0b1120|131c2e|111827|1f2937|18181b|09090b))['"]/gi)];
  const hardcodedDarkText = [...content.matchAll(/color:\s*['"](#(?:000(?:000)?|0f172a|1e293b|334155|475569|000|111827|1f2937|18181b|09090b))['"]/gi)];
  const hardcodedWhiteText = [...content.matchAll(/color:\s*['"](#fff(?:fff)?|white)['"]/gi)];
  const hardcodedBorder = [...content.matchAll(/border(?:Color)?:\s*['"][^'"]*(#(?:e2e8f0|e5e7eb|cbd5e1|d1d5db|243049|334155|e0e0e0|ccc|ddd))['"]/gi)];

  console.log(`Hardcoded White Backgrounds: ${hardcodedWhiteBg.length}`);
  console.log(`Hardcoded Dark Backgrounds: ${hardcodedDarkBg.length}`);
  console.log(`Hardcoded Dark Text: ${hardcodedDarkText.length}`);
  console.log(`Hardcoded White Text: ${hardcodedWhiteText.length}`);
  console.log(`Hardcoded Borders: ${hardcodedBorder.length}`);

  // Find sample lines where hardcoded dark text appears without variable
  const darkTextLines = [];
  content.split('\n').forEach((line, idx) => {
    if (/color:\s*['"]#(?:000|0f172a|1e293b|334155|475569|111827)['"]/i.test(line)) {
      darkTextLines.push({ line: idx + 1, code: line.trim() });
    }
  });
  console.log(`Sample Dark Text Lines (${darkTextLines.length}):`);
  darkTextLines.slice(0, 5).forEach(d => console.log(`  Line ${d.line}: ${d.code}`));
}

auditFile('frontend/src/pages/FarmerDashboard.jsx');
auditFile('frontend/src/pages/GovernmentDashboard.jsx');
