import React from 'react';

export const SquirrelSvg: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <svg
      viewBox="0 0 120 120"
      className={`w-24 h-24 select-none pointer-events-none ${className}`}
      aria-hidden="true"
    >
      {/* Branch underneath */}
      <path
        d="M 0 105 Q 60 102, 120 100"
        stroke="#5A3A28"
        strokeWidth="6"
        strokeLinecap="round"
      />

      {/* Bushy Tail (Curling up and over back) */}
      <path
        d="M 50 90 C 85 95, 115 80, 110 45 C 105 20, 85 10, 75 18 C 65 25, 75 45, 80 55 C 85 65, 75 80, 52 82 Z"
        fill="var(--squirrel, #B05A30)"
      />
      {/* Tail fluff highlight */}
      <path
        d="M 105 45 C 102 28, 88 20, 80 25"
        stroke="#E89650"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />

      {/* Body */}
      <ellipse cx="48" cy="78" rx="16" ry="20" fill="var(--squirrel, #B05A30)" />
      {/* Cream Chest */}
      <ellipse cx="40" cy="80" rx="9" ry="14" fill="#F4F1E8" />

      {/* Head */}
      <circle cx="42" cy="54" r="13" fill="var(--squirrel, #B05A30)" />
      {/* Ear */}
      <path d="M 44 43 L 49 32 L 53 44 Z" fill="var(--squirrel, #B05A30)" />
      <path d="M 46 41 L 49 36 L 51 42 Z" fill="#E89650" />

      {/* Eye & Nose */}
      <circle cx="36" cy="52" r="2.2" fill="#1F2A44" />
      <circle cx="35" cy="51" r="0.6" fill="#FFFFFF" />
      <circle cx="30" cy="56" r="1.5" fill="#1F2A44" />

      {/* Paws holding acorn */}
      <ellipse cx="32" cy="72" rx="4" ry="3" fill="#B05A30" />
      {/* Acorn */}
      <ellipse cx="28" cy="70" rx="4" ry="5" fill="#A8693A" />
      <path d="M 24 67 Q 28 64, 32 67" stroke="#5A3A28" strokeWidth="1.5" fill="#5A3A28" />

      {/* Foot perched on branch */}
      <ellipse cx="45" cy="98" rx="7" ry="4" fill="#8D5528" />
    </svg>
  );
};
