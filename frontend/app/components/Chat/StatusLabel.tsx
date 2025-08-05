"use client";

import type React from "react";

interface StatusLabelProps {
  status: boolean;
  trueText: string;
  falseText: string;
}

const StatusLabel: React.FC<StatusLabelProps> = ({
  status,
  trueText,
  falseText,
}) => {
  return (
    <div
      className={`p-2 rounded-lg text-text-verba text-sm ${status ? "bg-secondary-verba" : "bg-bg-alt-verba text-text-alt-verba"}`}
    >
      <p
        className={`text-xs ${status ? "text-text-verba" : "text-text-alt-verba"}`}
      >
        {status ? trueText : falseText}
      </p>
    </div>
  );
};

export default StatusLabel;
