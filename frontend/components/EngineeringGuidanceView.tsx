"use client";

import { useState } from "react";

/**
 * Mirrors backend/app/reasoning/schemas.py::EngineeringGuidance exactly.
 * Kept local to this component (not added to lib/api-client.ts) — the
 * client's Message type only needs to know structured_output can hold
 * one of these; it doesn't need the shape's internals.
 */
export interface EngineeringGuidance {
  clarifying_questions: string[];
  engineering_reasoning: string;
  preliminary_calculations: Record<string, string | number | boolean>;
  material_suggestions: string[];
  manufacturing_suggestions: string[];
  recommended_next_steps: string[];
}

interface EngineeringGuidanceViewProps {
  data: EngineeringGuidance;
  rawText: string;
}

export default function EngineeringGuidanceView({
  data,
  rawText,
}: EngineeringGuidanceViewProps) {
  const [showRaw, setShowRaw] = useState(false);

  const calculationEntries = Object.entries(data.preliminary_calculations);

  return (
    <div className="flex flex-col gap-3">
      {/* 1. engineering_reasoning — always present, min_length=1 in schema */}
      <p>{data.engineering_reasoning}</p>

      {/* 2. preliminary_calculations — hidden if empty dict */}
      {calculationEntries.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-gray-600">
            Calculations
          </span>
          <div className="border rounded divide-y">
            {calculationEntries.map(([key, value]) => (
              <div key={key} className="flex justify-between px-3 py-1 text-sm">
                <span className="text-gray-600">{key}</span>
                <span>{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. material_suggestions — hidden if [] */}
      {data.material_suggestions.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-gray-600">
            Material suggestions
          </span>
          <ul className="list-disc list-inside">
            {data.material_suggestions.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. manufacturing_suggestions — hidden if [] */}
      {data.manufacturing_suggestions.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-gray-600">
            Manufacturing suggestions
          </span>
          <ul className="list-disc list-inside">
            {data.manufacturing_suggestions.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 5. recommended_next_steps — numbered, hidden if [] */}
      {data.recommended_next_steps.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-gray-600">
            Recommended next steps
          </span>
          <ol className="list-decimal list-inside">
            {data.recommended_next_steps.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ol>
        </div>
      )}

      {/* 6. clarifying_questions — hidden if [], rendered last */}
      {data.clarifying_questions.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-gray-600">
            Clarifying questions
          </span>
          <ul className="list-disc list-inside">
            {data.clarifying_questions.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 7. Collapsible raw response — always available, collapsed by default */}
      <div>
        <button
          type="button"
          onClick={() => setShowRaw((prev) => !prev)}
          className="text-xs text-gray-600 border rounded px-2 py-1"
        >
          {showRaw ? "Hide raw response" : "View raw response"}
        </button>
        {showRaw && (
          <pre className="mt-2 border rounded p-2 text-xs whitespace-pre-wrap">
            {rawText}
          </pre>
        )}
      </div>
    </div>
  );
}
