import React, { useState } from 'react';

interface SymbolLogoProps {
  symbol: string;
  className?: string;
  size?: number;
}

const SymbolLogo: React.FC<SymbolLogoProps> = ({ symbol, className = '', size = 32 }) => {
  const [error, setError] = useState(false);
  const url = `https://img.logo.dev/ticker/${symbol}?token=pk_ZIh7vOJFQWWs8N0CkI74-Q&retina=true`;

  if (error) {
    return (
      <div
        className={`bg-gray-100 rounded-lg flex items-center justify-center ${className}`}
        style={{ width: size, height: size }}
      >
        <span className="text-xs font-bold text-gray-600">{symbol.slice(0, 2)}</span>
      </div>
    );
  }

  return (
    <img
      src={url}
      alt={`${symbol} logo`}
      className={`rounded-lg ${className}`}
      style={{ width: size, height: size }}
      onError={() => setError(true)}
    />
  );
};

export default SymbolLogo;
