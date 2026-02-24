"use client";

import { FileText, Cloud, Brain, Info } from "lucide-react";
import type { Report } from "@/lib/types";
import { formatDate } from "@/lib/utils";

interface ReportViewerProps {
  report: Report;
}

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

function Section({ title, icon, children }: SectionProps) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface-card p-5">
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h3 className="text-sm font-semibold text-gray-100">{title}</h3>
      </div>
      <div className="text-sm text-gray-300 leading-relaxed">{children}</div>
    </div>
  );
}

function DataRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value === null || value === undefined) return null;
  return (
    <div className="flex justify-between py-1.5 border-b border-surface-border last:border-0">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-xs text-gray-200 font-medium">{String(value)}</span>
    </div>
  );
}

export default function ReportViewer({ report }: ReportViewerProps) {
  const data = report.structured_data || {};
  const weather = data.weather as Record<string, unknown> | undefined;
  const analysis = data.analysis as Record<string, unknown> | undefined;
  const details = data.details as Record<string, unknown> | undefined;

  return (
    <div className="space-y-4">
      {/* Report Meta */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">
            Report: {report.report_type}
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Generated {formatDate(report.created_at)} by {report.generated_by}{" "}
            &middot; Version {report.version}
          </p>
        </div>
        {report.pdf_url && (
          <a
            href={report.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-surface-border bg-surface-elevated px-3 py-1.5 text-xs text-accent hover:text-accent-hover transition-colors"
          >
            Download PDF
          </a>
        )}
      </div>

      {/* Narrative / Summary */}
      <Section
        title="Summary"
        icon={<FileText className="h-4 w-4 text-accent" />}
      >
        <p className="whitespace-pre-wrap">{report.narrative}</p>
      </Section>

      {/* Details */}
      {details && Object.keys(details).length > 0 && (
        <Section
          title="Details"
          icon={<Info className="h-4 w-4 text-blue-400" />}
        >
          <div className="space-y-0">
            {Object.entries(details).map(([key, value]) => (
              <DataRow
                key={key}
                label={key
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())}
                value={typeof value === "object" ? JSON.stringify(value) : String(value)}
              />
            ))}
          </div>
        </Section>
      )}

      {/* Weather */}
      {weather && Object.keys(weather).length > 0 && (
        <Section
          title="Weather Conditions"
          icon={<Cloud className="h-4 w-4 text-sky-400" />}
        >
          <div className="space-y-0">
            {Object.entries(weather).map(([key, value]) => (
              <DataRow
                key={key}
                label={key
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())}
                value={typeof value === "object" ? JSON.stringify(value) : String(value)}
              />
            ))}
          </div>
        </Section>
      )}

      {/* Analysis */}
      {analysis && Object.keys(analysis).length > 0 && (
        <Section
          title="Analysis"
          icon={<Brain className="h-4 w-4 text-purple-400" />}
        >
          <div className="space-y-0">
            {Object.entries(analysis).map(([key, value]) => (
              <DataRow
                key={key}
                label={key
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())}
                value={typeof value === "object" ? JSON.stringify(value) : String(value)}
              />
            ))}
          </div>
        </Section>
      )}

      {/* Raw structured data fallback if no specific sections matched */}
      {!details && !weather && !analysis && Object.keys(data).length > 0 && (
        <Section
          title="Structured Data"
          icon={<Info className="h-4 w-4 text-gray-400" />}
        >
          <pre className="overflow-x-auto rounded bg-surface-elevated p-3 text-xs text-gray-300 font-mono">
            {JSON.stringify(data, null, 2)}
          </pre>
        </Section>
      )}
    </div>
  );
}
