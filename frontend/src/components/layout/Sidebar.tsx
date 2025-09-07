import React from 'react';
import {
  Home, Activity, List, BarChart3, Shield, Settings,
  TrendingUp, Brain, LogOut, ChevronLeft,
  Briefcase
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

export type Page = 'dashboard' | 'signals' | 'orders' | 'trades' | 'strategies' | 'exit-rules' | 'risk' | 'analytics' | 'settings';

interface SidebarProps {
  currentPage: Page;
  onPageChange: (page: Page) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  pendingSignalsCount: number;
}

interface MenuItem {
  id: Page;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | null;
  category: 'main' | 'trading' | 'analysis' | 'system';
}

const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onPageChange,
  isCollapsed,
  onToggleCollapse,
  pendingSignalsCount
}) => {
  const { user, logout } = useAuth();

  const menuCategories = {
    main: {
      title: 'Overview',
      items: [
        {
          id: 'dashboard' as Page,
          name: 'Dashboard',
          icon: Home,
          badge: null,
          category: 'main' as const
        }
      ]
    },
    trading: {
      title: 'Trading',
      items: [
        {
          id: 'signals' as Page,
          name: 'Signals',
          icon: Activity,
          badge: pendingSignalsCount > 0 ? pendingSignalsCount.toString() : null,
          category: 'trading' as const
        },
        {
          id: 'orders' as Page,
          name: 'Orders',
          icon: List,
          badge: null,
          category: 'trading' as const
        },
        {
          id: 'trades' as Page,
          name: 'Trades',
          icon: TrendingUp,
          badge: null,
          category: 'trading' as const
        },
        {
          id: 'strategies' as Page,
          name: 'Strategies',
          icon: Brain,
          badge: null,
          category: 'trading' as const
        },
        {
          id: 'exit-rules' as Page,
          name: 'Exit Rules',
          icon: Settings,
          badge: null,
          category: 'trading' as const
        }
      ]
    },
    analysis: {
      title: 'Analysis',
      items: [
        {
          id: 'analytics' as Page,
          name: 'Analytics',
          icon: BarChart3,
          badge: null,
          category: 'analysis' as const
        },
        {
          id: 'risk' as Page,
          name: 'Risk',
          icon: Shield,
          badge: null,
          category: 'analysis' as const
        }
      ]
    },
    system: {
      title: 'System',
      items: [
        {
          id: 'settings' as Page,
          name: 'Settings',
          icon: Settings,
          badge: null,
          category: 'system' as const
        }
      ]
    }
  };

  const renderMenuItem = (item: MenuItem) => {
    const Icon = item.icon;
    const isActive = currentPage === item.id;

    return (
      <button
        key={item.id}
        onClick={() => onPageChange(item.id)}
        className={`
          group relative w-full flex items-center rounded-xl transition-all duration-200
          ${isCollapsed ? 'px-3 py-3 justify-center' : 'px-4 py-3'}
          ${isActive
            ? 'bg-primary-50 text-primary-700 shadow-soft border border-primary-100'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }
        `}
      >
        <div className={`flex-shrink-0 ${isActive ? 'text-primary-600' : 'text-slate-500 group-hover:text-slate-700'}`}>
          <Icon className="h-5 w-5" />
        </div>
        
        {!isCollapsed && (
          <>
            <span className="ml-3 text-sm font-medium truncate">
              {item.name}
            </span>
            {item.badge && (
              <span className="ml-auto flex-shrink-0 bg-primary-100 text-primary-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                {item.badge}
              </span>
            )}
          </>
        )}

        {/* Tooltip para collapsed sidebar */}
        {isCollapsed && (
          <div className="absolute left-full ml-2 px-3 py-2 bg-slate-900 text-white text-sm rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 whitespace-nowrap">
            {item.name}
            {item.badge && (
              <span className="ml-2 bg-primary-600 text-white text-xs px-2 py-0.5 rounded-full">
                {item.badge}
              </span>
            )}
          </div>
        )}
      </button>
    );
  };

  return (
    <div className={`
      bg-white border-r border-slate-200 flex flex-col h-full transition-all duration-300 relative
      ${isCollapsed ? 'w-20' : 'w-72'}
    `}>
      {/* Header */}
      <div className={`flex items-center justify-between p-6 border-b border-slate-100 ${isCollapsed ? 'px-4' : ''}`}>
        {!isCollapsed && (
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-primary-700 rounded-xl flex items-center justify-center shadow-soft">
              <Briefcase className="h-5 w-5 text-white" />
            </div>
            <div className="ml-3">
              <h1 className="text-lg font-bold text-slate-900">TradingBot</h1>
              <p className="text-xs text-slate-500">Professional Suite</p>
            </div>
          </div>
        )}
        
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors duration-200"
        >
          <ChevronLeft className={`h-4 w-4 transition-transform duration-300 ${isCollapsed ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* User Profile */}
      {!isCollapsed && (
        <div className="p-4 border-b border-slate-100">
          <div className="flex items-center p-3 bg-slate-50 rounded-xl">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-semibold text-sm">
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </span>
            </div>
            <div className="ml-3 flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900 truncate">
                {user?.full_name || user?.username}
              </p>
              <div className="flex items-center mt-1">
                <div className="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
                <span className="text-xs text-slate-500">Online</span>
                {user?.is_admin && (
                  <span className="ml-2 text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-medium">
                    Admin
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-6 overflow-y-auto scrollbar-hide">
        {Object.entries(menuCategories).map(([categoryKey, category]) => (
          <div key={categoryKey}>
            {!isCollapsed && (
              <h3 className="px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                {category.title}
              </h3>
            )}
            <div className="space-y-1">
              {category.items.map(renderMenuItem)}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-100">
        <button
          onClick={logout}
          className={`
            group w-full flex items-center rounded-xl px-4 py-3 text-sm font-medium
            text-slate-600 hover:text-error-700 hover:bg-error-50 transition-all duration-200
            ${isCollapsed ? 'justify-center px-3' : ''}
          `}
        >
          <LogOut className="h-5 w-5 text-slate-400 group-hover:text-error-600" />
          {!isCollapsed && <span className="ml-3">Sign Out</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;

