import React from 'react';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import BalanceIcon from '@mui/icons-material/Balance';
import ComputerIcon from '@mui/icons-material/Computer';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import ElectricBoltIcon from '@mui/icons-material/ElectricBolt';
import { COMPANY_NAMES } from '../utils/companyNames';

export default function Sidebar({ companies, onCompanySelect, onQuickAction }) {
  const quickActions = [
    { label: 'Revenue Trends', icon: TrendingUpIcon },
    { label: 'Profitability', icon: AttachMoneyIcon },
    { label: 'Leverage', icon: BalanceIcon },
  ];

  const sectors = [
    { label: 'Technology', icon: ComputerIcon },
    { label: 'Finance', icon: AccountBalanceIcon },
    { label: 'Healthcare', icon: LocalHospitalIcon },
    { label: 'Energy', icon: ElectricBoltIcon },
  ];

  return (
    <div className="w-64 bg-dark-bg-secondary flex flex-col border-r border-dark-border h-screen">
      
      {/* QUICK ACTIONS - Top Section */}
      <div className="p-4 border-b border-dark-border">
        <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-3">
          Quick Actions
        </h3>
        <div className="space-y-2">
          {quickActions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <button
                key={idx}
                onClick={() => onQuickAction && onQuickAction(action.label)}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-dark-card hover:bg-dark-border transition-colors text-dark-text text-sm font-medium border border-dark-border"
              >
                <Icon style={{ fontSize: '18px', color: '#6366f1' }} />
                {action.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* SECTORS - Middle Section */}
      <div className="p-4 border-b border-dark-border">
        <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-3">
          Sectors
        </h3>
        <div className="space-y-2">
          {sectors.map((sector, idx) => {
            const Icon = sector.icon;
            return (
              <button
                key={idx}
                onClick={() => onQuickAction && onQuickAction(`Sector: ${sector.label}`)}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-dark-card hover:bg-dark-border transition-colors text-dark-text text-sm font-medium border border-dark-border"
              >
                <Icon style={{ fontSize: '18px', color: '#6366f1' }} />
                {sector.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* COMPANIES - Scrollable Section */}
      <div className="flex-1 flex flex-col px-4 py-4 overflow-hidden">
        <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-2">
          Companies
        </h3>
        <div className="flex-1 overflow-y-auto space-y-1 pr-2">
          {companies.map((ticker) => (
            <button
              key={ticker}
              onClick={() => onCompanySelect && onCompanySelect(ticker)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-dark-border transition-colors text-dark-text text-sm font-medium text-left"
            >
              <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0"></span>
              <span className="truncate">{COMPANY_NAMES[ticker] || ticker}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
