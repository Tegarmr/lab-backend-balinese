import { useState } from 'react';

/**
 * Collapsible accordion step for intermediate results.
 */
export default function CollapsibleStep({ title, icon, stepNumber, defaultOpen = false, badge, children }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="glass-card overflow-hidden" id={`step-${stepNumber}`}>
      {/* Header */}
      <button
        className="step-header w-full flex items-center gap-3 px-5 py-4 text-left"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        id={`step-${stepNumber}-toggle`}
      >
        {/* Chevron */}
        <svg
          className={`w-4 h-4 text-dark-text-muted transition-transform duration-300 flex-shrink-0 ${isOpen ? 'rotate-90' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>

        {/* Icon */}
        <span className="text-lg flex-shrink-0">{icon}</span>

        {/* Title */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs text-dark-text-muted font-mono">
              Step {stepNumber}
            </span>
            <span className="text-sm font-medium text-dark-text truncate">
              {title}
            </span>
          </div>
        </div>

        {/* Badge */}
        {badge && (
          <span className="detection-badge flex-shrink-0">
            {badge}
          </span>
        )}
      </button>

      {/* Content */}
      <div className={`step-content ${isOpen ? 'expanded' : 'collapsed'}`}>
        <div className="px-5 pb-5 pt-1">
          {children}
        </div>
      </div>
    </div>
  );
}
