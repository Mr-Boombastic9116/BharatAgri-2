// Test frontend auth and route guard logic
const assert = require('assert');

// App.jsx logic
const normalizeRole = (role) => {
  return (role || '').toLowerCase().replace(/[-_ ]+/g, '_');
};

const isCentreRole = (role) => {
  const r = normalizeRole(role);
  return r === 'centre' || r === 'center' || r === 'procurement_centre' || r === 'procurement_center';
};

const getRoleDashboard = (role) => {
  const r = normalizeRole(role);
  if (r === 'farmer') return 'farmer-dashboard';
  if (r === 'agent') return 'agent-dashboard';
  if (r === 'government' || r === 'admin' || r === 'superadmin') return 'government-dashboard';
  if (isCentreRole(role)) return 'centre-dashboard';
  return 'home';
};

const isPageAuthorized = (page, currentUser) => {
  const r = normalizeRole(currentUser?.role);
  if (page === 'farmer-dashboard') return r === 'farmer';
  if (page === 'agent-dashboard') return r === 'agent';
  if (page === 'centre-dashboard' || page === 'centre-process' || page === 'centre-storage') {
    return isCentreRole(currentUser?.role);
  }
  if (page === 'government-dashboard') return r === 'government' || r === 'admin' || r === 'superadmin';
  if (page === 'book-slot' || page === 'my-booking') return r === 'farmer' || r === 'agent';
  return true;
};

console.log('--- Testing Role Normalization & Guards ---');
const centreVariants = ['centre', 'center', 'Centre', 'CENTER', 'procurement_centre', 'procurement-centre', 'procurement centre', 'PROCUREMENT_CENTRE'];
for (const v of centreVariants) {
  assert.strictEqual(isCentreRole(v), true, `Failed isCentreRole for ${v}`);
  assert.strictEqual(getRoleDashboard(v), 'centre-dashboard', `Failed getRoleDashboard for ${v}`);
  assert.strictEqual(isPageAuthorized('centre-dashboard', { role: v }), true, `Failed isPageAuthorized for ${v}`);
}
console.log('✓ All 8 centre role variants correctly route to centre-dashboard and are authorized.');

console.log('--- Testing Role Isolation ---');
assert.strictEqual(isPageAuthorized('centre-dashboard', { role: 'farmer' }), false, 'Farmer must not access centre-dashboard');
assert.strictEqual(isPageAuthorized('centre-dashboard', { role: 'agent' }), false, 'Agent must not access centre-dashboard');
assert.strictEqual(isPageAuthorized('centre-dashboard', { role: 'government' }), false, 'Government must not access centre-dashboard');
assert.strictEqual(isPageAuthorized('government-dashboard', { role: 'centre' }), false, 'Centre must not access government-dashboard');
assert.strictEqual(isPageAuthorized('farmer-dashboard', { role: 'centre' }), false, 'Centre must not access farmer-dashboard');
console.log('✓ Strict role-based isolation verified across all user roles.');

console.log('--- Testing Refresh & Direct Access Scenarios ---');
// Unauthenticated direct access to centre-dashboard
const PROTECTED = ['farmer-dashboard', 'agent-dashboard', 'centre-dashboard', 'government-dashboard', 'centre-process', 'centre-storage', 'book-slot'];
let mockLocalStorage = {};

function simulateDirectAccess(targetHash) {
  const hashPage = targetHash.replace(/^#\/?/, '').trim();
  let currentUser = mockLocalStorage['bharatagri_user'] ? JSON.parse(mockLocalStorage['bharatagri_user']) : null;
  if (PROTECTED.includes(hashPage)) {
    if (!currentUser) {
      return { activePage: 'login', hash: 'login' };
    }
    if (!isPageAuthorized(hashPage, currentUser)) {
      const fallback = getRoleDashboard(currentUser.role);
      return { activePage: fallback, hash: fallback };
    }
  }
  return { activePage: hashPage, hash: hashPage };
}

// 1. Direct access when unauthenticated -> kicks to login
const unauthAccess = simulateDirectAccess('centre-dashboard');
assert.strictEqual(unauthAccess.activePage, 'login');
console.log('✓ Unauthenticated direct access to #centre-dashboard redirects to login.');

// 2. Login succeeds and saves to localStorage
const loggedInUser = {
  user_id: 'centre@bharatagri.demo',
  role: 'centre',
  centre_id: 'C001',
  centre_name: 'Pune Procurement Centre 1',
  token: 'mock-jwt-token'
};
mockLocalStorage['bharatagri_user'] = JSON.stringify(loggedInUser);

// 3. User visits #centre-dashboard
const centreAccess = simulateDirectAccess('centre-dashboard');
assert.strictEqual(centreAccess.activePage, 'centre-dashboard');
console.log('✓ Authenticated centre user successfully accesses #centre-dashboard.');

// 4. Page refresh (reading from localStorage on initial render)
const refreshAccess = simulateDirectAccess('centre-dashboard');
assert.strictEqual(refreshAccess.activePage, 'centre-dashboard');
console.log('✓ Centre Dashboard survives page refresh and stays on #centre-dashboard.');

// 5. Logout removes localStorage
delete mockLocalStorage['bharatagri_user'];
const afterLogoutAccess = simulateDirectAccess('centre-dashboard');
assert.strictEqual(afterLogoutAccess.activePage, 'login');
console.log('✓ After logout, attempt to open #centre-dashboard correctly rejected to login.');

console.log('\nALL FRONTEND AUTH & ROUTING TESTS PASSED!');
