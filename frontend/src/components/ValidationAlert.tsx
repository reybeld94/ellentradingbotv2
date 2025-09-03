import React from 'react';

interface ValidationAlertProps {
  issues: any[];
  onClose: () => void;
  onCleanup: (dryRun: boolean) => Promise<any>;
}

const ValidationAlert: React.FC<ValidationAlertProps> = ({ issues, onClose, onCleanup }) => {
  if (issues.length === 0) return null;

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-yellow-800 font-semibold">
          ⚠️ Validation Issues Found ({issues.length})
        </h3>
        <button onClick={onClose} className="text-yellow-600 hover:text-yellow-800">✕</button>
      </div>

      <div className="space-y-2 mb-4">
        {issues.slice(0, 5).map((issue, idx) => (
          <div key={idx} className="text-sm text-yellow-700">
            • {issue.symbol}: {issue.issues.join(', ')}
          </div>
        ))}
        {issues.length > 5 && (
          <div className="text-sm text-yellow-600">
            ...and {issues.length - 5} more issues
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onCleanup(true)}
          className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded text-sm hover:bg-yellow-200"
        >
          Preview Cleanup
        </button>
        <button
          onClick={() => onCleanup(false)}
          className="px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200"
        >
          Clean Up Now
        </button>
      </div>
    </div>
  );
};

export default ValidationAlert;
