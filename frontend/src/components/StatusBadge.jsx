import React from 'react';

export default function StatusBadge({ status }) {
  const raw = status || 'PENDING';
  const normalized = raw.toLowerCase().replace(/[\s_-]+/g, '');
  
  let badgeClass = 'badge-pending';
  if (['confirmed', 'booked'].includes(normalized)) badgeClass = 'badge-confirmed';
  else if (['checkedin', 'verified'].includes(normalized)) badgeClass = 'badge-verified';
  else if (['arrived'].includes(normalized)) badgeClass = 'badge-arrived';
  else if (['received', 'collected'].includes(normalized)) badgeClass = 'badge-received';
  else if (['qualitychecked'].includes(normalized)) badgeClass = 'badge-quality-checked';
  else if (['weighed'].includes(normalized)) badgeClass = 'badge-weighed';
  else if (['stored', 'procured'].includes(normalized)) badgeClass = 'badge-stored';
  else if (['paymentinitiated'].includes(normalized)) badgeClass = 'badge-payment-initiated';
  else if (['paid', 'completed'].includes(normalized)) badgeClass = 'badge-paid';
  else if (['rejected', 'cancelled', 'expired'].includes(normalized)) badgeClass = 'badge-rejected';
  else if (['critical'].includes(normalized)) badgeClass = 'badge-critical';
  else if (['high'].includes(normalized)) badgeClass = 'badge-high';
  else if (['medium'].includes(normalized)) badgeClass = 'badge-medium';
  else if (['low', 'normal'].includes(normalized)) badgeClass = 'badge-low';

  return (
    <span className={`badge ${badgeClass}`}>
      {raw.replace(/_/g, ' ')}
    </span>
  );
}
