import type { FC } from "react";

interface RobotIconProps {
  size?: "lg" | "sm";
}

export const RobotIcon: FC<RobotIconProps> = ({ size = "sm" }) => {
  if (size === "lg") {
    return (
      <svg
        width="56"
        height="68"
        viewBox="0 0 56 68"
        fill="none"
        aria-hidden="true"
        className="robot-float"
      >
        {/* Antenna stem */}
        <line x1="28" y1="10" x2="28" y2="2" stroke="#00ffff" strokeWidth="1.5" strokeLinecap="round"/>
        {/* Antenna tip — flickers */}
        <circle cx="28" cy="1.5" r="2" fill="#00ffff" className="robot-antenna"/>

        {/* Side ear left */}
        <line x1="6" y1="28" x2="1" y2="28" stroke="#00ffff" strokeWidth="1.5" strokeLinecap="round"/>
        <rect x="0" y="26" width="2" height="4" rx="1" fill="#00ffff" opacity="0.7"/>

        {/* Side ear right */}
        <line x1="50" y1="28" x2="55" y2="28" stroke="#00ffff" strokeWidth="1.5" strokeLinecap="round"/>
        <rect x="54" y="26" width="2" height="4" rx="1" fill="#00ffff" opacity="0.7"/>

        {/* Main head */}
        <rect x="6" y="10" width="44" height="44" rx="6" fill="#0a0a1a" stroke="#00ffff" strokeWidth="1.2"/>

        {/* Inner face panel */}
        <rect x="11" y="15" width="34" height="34" rx="4" fill="#050510" stroke="#7c3aed" strokeWidth="0.8"/>

        {/* Left eye outer ring */}
        <circle cx="21" cy="30" r="7" fill="#001515" stroke="#00ffff" strokeWidth="1"/>
        {/* Left eye iris — neon glow */}
        <circle cx="21" cy="30" r="4.5" fill="#00ffff" className="robot-eye-glow"/>
        {/* Left eye pupil */}
        <circle cx="21" cy="30" r="2" fill="#001515"/>
        {/* Left eye shine */}
        <circle cx="22.5" cy="28.5" r="1" fill="white" opacity="0.8"/>

        {/* Right eye outer ring */}
        <circle cx="35" cy="30" r="7" fill="#001515" stroke="#00ffff" strokeWidth="1"/>
        {/* Right eye iris — neon glow */}
        <circle cx="35" cy="30" r="4.5" fill="#00ffff" className="robot-eye-glow"/>
        {/* Right eye pupil */}
        <circle cx="35" cy="30" r="2" fill="#001515"/>
        {/* Right eye shine */}
        <circle cx="36.5" cy="28.5" r="1" fill="white" opacity="0.8"/>

        {/* Mouth panel */}
        <rect x="14" y="42" width="28" height="5" rx="2" fill="#001515" stroke="#00ffff" strokeWidth="0.8"/>
        {/* Scan line inside mouth — animates */}
        <rect x="15" y="43.5" width="26" height="2" rx="1" fill="#001515"/>
        <rect x="15" y="43.5" width="10" height="2" rx="1" fill="#00ffff" opacity="0.85" className="robot-scan-line"/>

        {/* Bottom connector */}
        <rect x="20" y="54" width="16" height="4" rx="2" fill="#0a0a1a" stroke="#7c3aed" strokeWidth="0.8"/>
        <line x1="28" y1="58" x2="28" y2="64" stroke="#7c3aed" strokeWidth="1.2" strokeLinecap="round"/>
        <rect x="22" y="64" width="12" height="4" rx="2" fill="#0a0a1a" stroke="#7c3aed" strokeWidth="0.8"/>
      </svg>
    );
  }

  // "sm" variant — avatar
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      {/* Antenna */}
      <line x1="12" y1="5" x2="12" y2="2" stroke="#00ffff" strokeWidth="1.5" strokeLinecap="round"/>
      <circle cx="12" cy="1.5" r="1" fill="#00ffff"/>
      {/* Head */}
      <rect x="3" y="5" width="18" height="14" rx="3" fill="#0a0a1a" stroke="#00ffff" strokeWidth="1.2"/>
      {/* Eyes */}
      <circle cx="9" cy="11" r="2.5" fill="#00ffff" className="robot-eye-glow"/>
      <circle cx="9" cy="11" r="1" fill="#001515"/>
      <circle cx="15" cy="11" r="2.5" fill="#00ffff" className="robot-eye-glow"/>
      <circle cx="15" cy="11" r="1" fill="#001515"/>
      {/* Mouth */}
      <rect x="7" y="15" width="10" height="2" rx="1" fill="#001515" stroke="#00ffff" strokeWidth="0.6"/>
      <rect x="7" y="15.3" width="4" height="1.2" rx="0.6" fill="#00ffff" opacity="0.8"/>
    </svg>
  );
};
