import React from 'react';

interface AveniqLogoProps {
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
  className?: string;
}

export const AveniqLogo: React.FC<AveniqLogoProps> = ({
  size = 'md',
  showSubtitle = true,
  className = '',
}) => {
  const iconSizes = {
    sm: 28,
    md: 36,
    lg: 44,
  };

  const dim = iconSizes[size];

  return (
    <div className={`aveniq-brand-lockup aveniq-brand-${size} ${className}`}>
      <div className="aveniq-logo-emblem" style={{ width: dim, height: dim }}>
        <svg
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="aveniq-svg"
        >
          <rect width="40" height="40" rx="10" fill="url(#bgGrad)" />
          {/* Outer faceted geometric diamond */}
          <path
            d="M20 5L33 18L20 31L7 18Z"
            stroke="url(#outerStroke)"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Inner targeting core */}
          <path
            d="M20 11L27 18L20 25L13 18Z"
            stroke="url(#innerStroke)"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.85"
          />
          {/* Optical central aperture */}
          <circle cx="20" cy="18" r="2.8" fill="url(#coreGlow)" />
          {/* Subtle pulse crosshairs */}
          <line x1="20" y1="2" x2="20" y2="6" stroke="#818CF8" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="20" y1="30" x2="20" y2="34" stroke="#38BDF8" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="4" y1="18" x2="8" y2="18" stroke="#818CF8" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="32" y1="18" x2="36" y2="18" stroke="#38BDF8" strokeWidth="1.5" strokeLinecap="round" />

          <defs>
            <linearGradient id="bgGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
              <stop stopColor="#0F172A" />
              <stop offset="1" stopColor="#0B0F19" />
            </linearGradient>
            <linearGradient id="outerStroke" x1="7" y1="5" x2="33" y2="31" gradientUnits="userSpaceOnUse">
              <stop stopColor="#6366F1" />
              <stop offset="0.5" stopColor="#818CF8" />
              <stop offset="1" stopColor="#06B6D4" />
            </linearGradient>
            <linearGradient id="innerStroke" x1="13" y1="11" x2="27" y2="25" gradientUnits="userSpaceOnUse">
              <stop stopColor="#A5B4FC" />
              <stop offset="1" stopColor="#38BDF8" />
            </linearGradient>
            <radialGradient id="coreGlow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(20 18) rotate(90) scale(2.8)">
              <stop stopColor="#38BDF8" />
              <stop offset="1" stopColor="#4F46E5" />
            </radialGradient>
          </defs>
        </svg>
      </div>

      <div className="aveniq-brand-text">
        <div className="aveniq-brand-row">
          <span className="aveniq-wordmark">AVENIQ</span>
          <span className="aveniq-status-badge">DATA ENGINE</span>
        </div>
        {showSubtitle && (
          <span className="aveniq-product-tag">Data Scraper &bull; Enterprise Open Data</span>
        )}
      </div>
    </div>
  );
};
