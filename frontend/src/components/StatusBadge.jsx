import React from 'react';

export default function StatusBadge({ status }) {
  const normalized = (status || 'Pending').toLowerCase();
  
  let badgeClass = 'badge-pending';
  if (normalized === 'confirmed') badgeClass = 'badge-confirmed';
  if (normalized === 'rejected') badgeClass = 'badge-rejected';
  if (normalized === 'arrived') badgeClass = 'badge-arrived';

  return (
    <span className={`badge ${badgeClass}`}>
      {status}
    </span>
  );
}
