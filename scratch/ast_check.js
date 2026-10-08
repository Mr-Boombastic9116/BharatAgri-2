const fs = require('fs');
const parser = require('../frontend/node_modules/@babel/parser');

const code = fs.readFileSync('frontend/src/pages/CentreDashboard.jsx', 'utf8');

const ast = parser.parse(code, {
  sourceType: 'module',
  plugins: ['jsx']
});

const globals = new Set([
  'window', 'document', 'console', 'localStorage', 'sessionStorage', 'setTimeout', 'clearTimeout',
  'setInterval', 'clearInterval', 'fetch', 'Date', 'Promise', 'Math', 'JSON', 'Array', 'Object',
  'String', 'Number', 'Boolean', 'RegExp', 'Error', 'parseInt', 'parseFloat', 'isNaN', 'isFinite',
  'encodeURIComponent', 'decodeURIComponent', 'Set', 'Map', 'Intl', 'URL', 'navigator', 'alert',
  'undefined', 'null', 'NaN', 'Infinity', 'navigator', 'Intl'
]);

const scopes = [new Set(globals)];

function currentScopeHas(name) {
  for (let i = scopes.length - 1; i >= 0; i--) {
    if (scopes[i].has(name)) return true;
  }
  return false;
}

const undeclared = new Set();

function walk(node, parent) {
  if (!node || typeof node !== 'object') return;

  const isScope = [
    'FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression',
    'BlockStatement', 'ForStatement', 'ForInStatement', 'ForOfStatement',
    'CatchClause'
  ].includes(node.type);

  if (isScope) {
    scopes.push(new Set());
  }

  // Register declarations
  if (node.type === 'ImportSpecifier' || node.type === 'ImportDefaultSpecifier' || node.type === 'ImportNamespaceSpecifier') {
    scopes[scopes.length - 1].add(node.local.name);
  } else if (node.type === 'VariableDeclarator' && node.id) {
    registerPattern(node.id, scopes[scopes.length - 1]);
  } else if (node.type === 'FunctionDeclaration' && node.id) {
    scopes[scopes.length - 1].add(node.id.name);
  } else if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(node.type)) {
    if (node.params) {
      node.params.forEach(p => registerPattern(p, scopes[scopes.length - 1]));
    }
  } else if (node.type === 'CatchClause' && node.param) {
    registerPattern(node.param, scopes[scopes.length - 1]);
  }

  // Check identifier usages
  if (node.type === 'Identifier') {
    // Only check if it's a reference to a variable, NOT a property key (obj.key or { key: val }), NOT a declaration, NOT a label
    const isProp = parent && (
      (parent.type === 'MemberExpression' && parent.property === node && !parent.computed) ||
      (parent.type === 'OptionalMemberExpression' && parent.property === node && !parent.computed) ||
      (parent.type === 'ObjectProperty' && parent.key === node && !parent.computed) ||
      (parent.type === 'ObjectMethod' && parent.key === node && !parent.computed) ||
      (parent.type === 'VariableDeclarator' && parent.id === node) ||
      (parent.type === 'FunctionDeclaration' && parent.id === node) ||
      (parent.type === 'ImportSpecifier' && parent.imported === node && parent.local !== node)
    );
    if (!isProp) {
      if (!currentScopeHas(node.name)) {
        undeclared.add(node.name);
      }
    }
  } else if (node.type === 'JSXIdentifier') {
    if (/^[A-Z]/.test(node.name)) {
      if (!currentScopeHas(node.name)) {
        undeclared.add(node.name + ' (JSX tag)');
      }
    }
  }

  for (const key of Object.keys(node)) {
    if (key === 'comments' || key === 'loc') continue;
    const child = node[key];
    if (Array.isArray(child)) {
      child.forEach(c => walk(c, node));
    } else if (child && typeof child === 'object') {
      walk(child, node);
    }
  }

  if (isScope) {
    scopes.pop();
  }
}

function registerPattern(pattern, scope) {
  if (!pattern) return;
  if (pattern.type === 'Identifier') {
    scope.add(pattern.name);
  } else if (pattern.type === 'ObjectPattern') {
    pattern.properties.forEach(prop => {
      if (prop.type === 'Property' || prop.type === 'ObjectProperty') {
        registerPattern(prop.value, scope);
      } else if (prop.type === 'RestElement') {
        registerPattern(prop.argument, scope);
      }
    });
  } else if (pattern.type === 'ArrayPattern') {
    pattern.elements.forEach(el => el && registerPattern(el, scope));
  } else if (pattern.type === 'AssignmentPattern') {
    registerPattern(pattern.left, scope);
  } else if (pattern.type === 'RestElement') {
    registerPattern(pattern.argument, scope);
  }
}

walk(ast, null);

console.log('UNDECLARED IDENTIFIERS FOUND:');
for (const item of undeclared) {
  console.log(' - ' + item);
}
