import React from "react";

interface Props {
  children: React.ReactNode;
  className?: string;
  intensity?: number;
  glare?: boolean;
}

/**
 * Card3D provides crisp elevation and clean borders
 * WITHOUT applying CSS transforms (translate, rotate, perspective) to text,
 * guaranteeing 100% native Windows ClearType subpixel rendering with zero blur.
 */
export const Card3D: React.FC<Props> = ({
  children,
  className = "",
}) => {
  return (
    <div
      className={`transition-shadow duration-200 hover:shadow-md ${className}`}
    >
      {children}
    </div>
  );
};

export default Card3D;
