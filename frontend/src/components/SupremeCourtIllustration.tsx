import React from "react";

export const SupremeCourtIllustration: React.FC<{ className?: string }> = ({
  className = "w-40 h-28 opacity-65",
}) => {
  return (
    <svg
      viewBox="0 0 200 140"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="scGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#8d9f8b" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#556b53" stopOpacity="0.15" />
        </linearGradient>
      </defs>

      {/* Flag atop central dome */}
      <line x1="100" y1="6" x2="100" y2="24" stroke="#526351" strokeWidth="1.5" />
      <polygon points="100,7 114,11 100,15" fill="#f59e0b" fillOpacity="0.8" />

      {/* Main Dome */}
      <path
        d="M74 38 C74 18, 126 18, 126 38 Z"
        fill="url(#scGradient)"
        stroke="#526351"
        strokeWidth="1.2"
      />
      {/* Dome lantern / finial base */}
      <rect x="94" y="22" width="12" height="6" rx="2" fill="#697b67" fillOpacity="0.5" />

      {/* Dome drum / cornice */}
      <rect x="70" y="38" width="60" height="7" rx="1.5" fill="#758873" fillOpacity="0.3" stroke="#526351" strokeWidth="1" />
      {/* Drum vertical lines */}
      <line x1="82" y1="39" x2="82" y2="44" stroke="#526351" strokeWidth="0.8" />
      <line x1="94" y1="39" x2="94" y2="44" stroke="#526351" strokeWidth="0.8" />
      <line x1="106" y1="39" x2="106" y2="44" stroke="#526351" strokeWidth="0.8" />
      <line x1="118" y1="39" x2="118" y2="44" stroke="#526351" strokeWidth="0.8" />

      {/* Central Portico Pediment (Triangular Gable) */}
      <polygon
        points="100,45 62,64 138,64"
        fill="url(#scGradient)"
        stroke="#526351"
        strokeWidth="1.2"
      />
      {/* Pediment entablature */}
      <rect x="60" y="64" width="80" height="5" fill="#637561" fillOpacity="0.4" stroke="#526351" strokeWidth="0.8" />

      {/* Colonnade Pillars (Central Chamber) */}
      <rect x="67" y="69" width="4.5" height="34" rx="1" fill="#738671" fillOpacity="0.45" />
      <rect x="77" y="69" width="4.5" height="34" rx="1" fill="#738671" fillOpacity="0.45" />
      <rect x="87" y="69" width="4.5" height="34" rx="1" fill="#738671" fillOpacity="0.45" />
      <rect x="98" y="69" width="4.5" height="34" rx="1" fill="#738671" fillOpacity="0.45" />
      <rect x="108" y="69" width="4.5" height="34" rx="1" fill="#738671" fillOpacity="0.45" />
      <rect x="118" y="69" width="4.5" height="34" rx="1" fill="#738671" fillOpacity="0.45" />
      <rect x="128" y="69" width="4.5" height="34" rx="1" fill="#738671" fillOpacity="0.45" />

      {/* Side wings colonnade */}
      {/* Left Wing */}
      <rect x="16" y="70" width="44" height="4" fill="#637561" fillOpacity="0.3" stroke="#526351" strokeWidth="0.8" />
      <rect x="20" y="74" width="4" height="29" fill="#738671" fillOpacity="0.3" />
      <rect x="30" y="74" width="4" height="29" fill="#738671" fillOpacity="0.3" />
      <rect x="40" y="74" width="4" height="29" fill="#738671" fillOpacity="0.3" />
      <rect x="50" y="74" width="4" height="29" fill="#738671" fillOpacity="0.3" />

      {/* Right Wing */}
      <rect x="140" y="70" width="44" height="4" fill="#637561" fillOpacity="0.3" stroke="#526351" strokeWidth="0.8" />
      <rect x="146" y="74" width="4" height="29" fill="#738671" fillOpacity="0.3" />
      <rect x="156" y="74" width="4" height="29" fill="#738671" fillOpacity="0.3" />
      <rect x="166" y="74" width="4" height="29" fill="#738671" fillOpacity="0.3" />
      <rect x="176" y="74" width="4" height="29" fill="#738671" fillOpacity="0.3" />

      {/* Grand Base Plinth / Steps */}
      <rect x="12" y="103" width="176" height="5" rx="1" fill="#637561" fillOpacity="0.35" stroke="#526351" strokeWidth="0.8" />
      <rect x="8" y="108" width="184" height="5" rx="1" fill="#637561" fillOpacity="0.4" stroke="#526351" strokeWidth="0.8" />
      <rect x="4" y="113" width="192" height="6" rx="1" fill="#637561" fillOpacity="0.45" stroke="#526351" strokeWidth="0.8" />
    </svg>
  );
};

