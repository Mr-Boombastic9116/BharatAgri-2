const fs = require('fs');

const content = fs.readFileSync('frontend/src/pages/CentreDashboard.jsx', 'utf8');

// Parse all imports
const importRegex = /import\s+([\s\S]*?)\s+from\s+['"][^'"]+['"]/g;
let match;
const imported = new Set();
while ((match = importRegex.exec(content)) !== null) {
  let specifiers = match[1].trim();
  if (specifiers.startsWith('{') && specifiers.endsWith('}')) {
    specifiers.slice(1, -1).split(',').forEach(s => {
      s = s.trim();
      if (!s) return;
      if (s.includes(' as ')) {
        imported.add(s.split(/\s+as\s+/)[1].trim());
      } else {
        imported.add(s.trim());
      }
    });
  } else {
    imported.add(specifiers.trim());
  }
}

// Find all capitalized JSX tags
const jsxRegex = /<([A-Z][a-zA-Z0-9_]*)/g;
const jsxTags = new Set();
while ((match = jsxRegex.exec(content)) !== null) {
  jsxTags.add(match[1]);
}

console.log('Total Imported items:', imported.size);
console.log('Total JSX Capitalized tags:', jsxTags.size);

const missing = [];
for (const tag of jsxTags) {
  const isImported = imported.has(tag);
  const defRegex = new RegExp('(?:function|const|let|var|class)\\s+' + tag + '\\b');
  const isDefined = defRegex.test(content);
  if (!isImported && !isDefined) {
    missing.push(tag);
  }
}

console.log('MISSING JSX IDENTIFIERS:', missing);
