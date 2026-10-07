import React from 'react';

export const EagleSvg: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <svg
      viewBox="0 0 160 120"
      className={`w-28 h-20 fill-current select-none pointer-events-none ${className}`}
      aria-hidden="true"
    >
      {/* Eagle Wings */}
      <path
        d="M 12 18 C 35 15, 60 40, 75 58 C 72 45, 65 30, 60 15 C 57 8, 54 2, 50 0 C 42 12, 30 20, 12 18 Z"
        fill="#3D2B1F"
      />
      <path
        d="M 152 24 C 130 18, 102 42, 88 58 C 92 42, 100 26, 108 12 C 112 5, 118 0, 122 0 C 132 14, 142 22, 152 24 Z"
        fill="#3D2B1F"
      />
      {/* Wing primary feathers detail */}
      <path
        d="M 12 18 L 22 26 L 16 32 L 28 38 L 24 44 L 40 48 L 56 52"
        stroke="#271B14"
        strokeWidth="1.5"
        fill="#4A3525"
      />
      <path
        d="M 152 24 L 140 30 L 144 38 L 132 42 L 134 50 L 118 52 L 104 54"
        stroke="#271B14"
        strokeWidth="1.5"
        fill="#4A3525"
      />

      {/* Tail Feathers (white / cream) */}
      <polygon points="76,68 84,68 96,82 64,82" fill="#F4F1E8" stroke="#D9D4C6" strokeWidth="1" />

      {/* Body */}
      <ellipse cx="80" cy="56" rx="14" ry="18" fill="#4A3525" />

      {/* Head & Neck (white / cream) */}
      <circle cx="70" cy="46" r="8" fill="#F4F1E8" />

      {/* Beak & Eye (yellow/amber) */}
      <polygon points="62,45 66,43 66,49" fill="#E89650" />
      <circle cx="68" cy="45" r="1.2" fill="#1F2A44" />

      {/* Talons (yellow/amber) */}
      <line x1="75" y1="72" x2="73" y2="78" stroke="#E89650" strokeWidth="2" strokeLinecap="round" />
      <line x1="85" y1="72" x2="87" y2="78" stroke="#E89650" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
};
