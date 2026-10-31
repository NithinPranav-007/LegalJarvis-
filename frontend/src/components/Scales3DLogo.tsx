import React, { useState } from "react";
import { Scale } from "lucide-react";

export const Scales3DLogo: React.FC<{ className?: string }> = ({
  className = "w-9 h-9",
}) => {
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width - 0.5) * 24;
    const y = ((e.clientY - rect.top) / rect.height - 0.5) * -24;
    setCoords({ x, y });
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => {
        setHovered(false);
        setCoords({ x: 0, y: 0 });
      }}
      style={{
        perspective: "500px",
      }}
      className={`relative cursor-pointer ${className}`}
    >
      <div
        style={{
          transform: hovered
            ? `rotateX(${coords.y}deg) rotateY(${coords.x}deg) translateZ(8px) scale(1.08)`
            : "rotateX(0deg) rotateY(0deg) translateZ(0px) scale(1)",
          transition: hovered ? "transform 0.05s ease-out" : "transform 0.4s ease-out",
          transformStyle: "preserve-3d",
        }}
        className="w-full h-full rounded-xl bg-[#0f2c24] flex items-center justify-center text-white shadow-xs relative overflow-hidden"
      >
        <Scale className="h-5 w-5 stroke-[2.2] relative z-10" />

        {/* 3D Sheen Reflection */}
        {hovered && (
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/25 to-transparent pointer-events-none transition-transform duration-300"
            style={{
              transform: `translate(${coords.x * 1.5}px, ${-coords.y * 1.5}px)`,
            }}
          />
        )}
      </div>
    </div>
  );
};

