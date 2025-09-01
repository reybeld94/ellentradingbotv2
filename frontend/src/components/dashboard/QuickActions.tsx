import React from 'react';
import {
  Plus, Zap, BarChart3, Shield
} from 'lucide-react';

interface QuickActionsProps {
  onAction: (action: string) => void;
}

const QuickActions: React.FC<QuickActionsProps> = ({ onAction }) => {
  const actions = [
    {
      id: 'new-strategy',
      title: 'New Strategy',
      description: 'Create trading strategy',
      icon: Plus,
      color: 'bg-primary-500 hover:bg-primary-600',
      textColor: 'text-white'
    },
    {
      id: 'view-signals',
      title: 'View Signals',
      description: 'Check latest signals',
      icon: Zap,
      color: 'bg-warning-100 hover:bg-warning-200',
      textColor: 'text-warning-700'
    },
    {
      id: 'analytics',
      title: 'Analytics',
      description: 'Portfolio insights',
      icon: BarChart3,
      color: 'bg-success-100 hover:bg-success-200',
      textColor: 'text-success-700'
    },
    {
      id: 'risk-check',
      title: 'Risk Check',
      description: 'Review risk metrics',
      icon: Shield,
      color: 'bg-error-100 hover:bg-error-200',
      textColor: 'text-error-700'
    }
  ];

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h3>
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.id}
              onClick={() => onAction(action.id)}
              className={`p-4 rounded-xl text-left transition-all duration-200 ${action.color} group`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className={`h-5 w-5 ${action.textColor}`} />
              </div>
              <h4 className={`font-medium text-sm ${action.textColor} mb-1`}>
                {action.title}
              </h4>
              <p className={`text-xs ${action.textColor} opacity-75`}>
                {action.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default QuickActions;

