import React from "react";
import { Info } from "lucide-react";

interface Props {
  notice?: string | null;
}

export const TransitionNotice: React.FC<Props> = ({ notice }) => {
  const defaultNotice =
    "Statutory Transition Notice: With effect from 1 July 2024, the Indian Penal Code 1860 (IPC), Code of Criminal Procedure 1973 (CrPC), and Indian Evidence Act 1872 have been replaced by the Bharatiya Nyaya Sanhita 2023 (BNS), Bharatiya Nagarik Suraksha Sanhita 2023 (BNSS), and Bharatiya Sakshya Adhiniyam 2023 (BSA). Under Section 358 BNS / Section 531 BNSS, offences committed prior to 1 July 2024 continue to be governed by the repealed codes.";

  const text = notice || defaultNotice;

  return (
    <div
      role="alert"
      className="bg-indigo-50 border border-indigo-200 text-indigo-900 rounded-lg p-3 text-xs leading-relaxed flex items-start space-x-2.5 my-3 shadow-sm"
    >
      <Info className="h-4 w-4 text-indigo-600 flex-shrink-0 mt-0.5" />
      <div>
        <span className="font-bold uppercase tracking-wider text-[11px] block text-indigo-800 mb-0.5">
          Criminal Law Transition Notice (BNS / BNSS / BSA 2023)
        </span>
        <p>{text}</p>
      </div>
    </div>
  );
};

export default TransitionNotice;
