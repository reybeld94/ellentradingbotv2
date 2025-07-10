import { useState } from 'react';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Target, BarChart3, Maximize2, Download, RefreshCw } from 'lucide-react';
import type { EquityPoint } from './EquityCurveChart';

interface EquityCurveProProps {
  data?: EquityPoint[];
  initialEquity?: number;
}

const EquityCurvePro: React.FC<EquityCurveProProps> = ({ data = [] as EquityPoint[], initialEquity = 10000 }) => {
  const [timeframe, setTimeframe] = useState('1M');
  const [showDrawdown, setShowDrawdown] = useState(true);
  const [showBenchmark, setShowBenchmark] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Generar datos de ejemplo si no se proporcionan
  const generateEquityData = () => {
    const periods = timeframe === '1D' ? 48 : timeframe === '1W' ? 168 : timeframe === '1M' ? 720 : 2160;
    const data = [];
    let equity = initialEquity;
    let maxEquity = initialEquity;
    let benchmark = initialEquity;
    
    for (let i = 0; i < periods; i++) {
      // Simular movimientos de equity más realistas
      const volatility = 0.002;
      const trend = 0.0001;
      const change = (Math.random() - 0.48) * volatility + trend;
      equity *= (1 + change);
      
      // Benchmark (S&P 500 aproximado)
      const benchmarkChange = (Math.random() - 0.49) * 0.0015 + 0.00005;
      benchmark *= (1 + benchmarkChange);
      
      // Calcular max equity y drawdown
      if (equity > maxEquity) maxEquity = equity;
      const drawdown = ((equity - maxEquity) / maxEquity) * 100;
      
      const now = new Date();
      const timestamp = new Date(now.getTime() - (periods - i) * (timeframe === '1D' ? 30 : timeframe === '1W' ? 60 : 60) * 60000);
      
      data.push({
        timestamp: timestamp.toISOString(),
        time: timeframe === '1D' ? 
          timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) :
          timestamp.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        equity: parseFloat(equity.toFixed(2)),
        drawdown: parseFloat(drawdown.toFixed(2)),
        benchmark: parseFloat(benchmark.toFixed(2)),
        maxEquity: parseFloat(maxEquity.toFixed(2))
      });
    }
    return data;
  };

  const augmentData = () => {
    if (!data || data.length === 0) {
      return generateEquityData();
    }

    let maxEquity = initialEquity;
    let benchmark = initialEquity;

    return data.map((point: any) => {
      if (point.equity > maxEquity) {
        maxEquity = point.equity;
      }
      const drawdown = ((point.equity - maxEquity) / maxEquity) * 100;
      const ts = new Date(point.timestamp);
      const benchmarkChange = (Math.random() - 0.49) * 0.0015 + 0.00005;
      benchmark *= 1 + benchmarkChange;

      return {
        ...point,
        time:
          timeframe === '1D'
            ? ts.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
            : ts.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        drawdown: parseFloat(drawdown.toFixed(2)),
        benchmark: parseFloat(benchmark.toFixed(2)),
        maxEquity: parseFloat(maxEquity.toFixed(2)),
      };
    });
  };

  const equityData = augmentData();
  


  // Calcular métricas
  const currentEquity = equityData[equityData.length - 1]?.equity || initialEquity;
  const totalReturn = ((currentEquity - initialEquity) / initialEquity) * 100;
  const maxDrawdown = Math.min(...equityData.map(d => d.drawdown));
  const maxEquity = Math.max(...equityData.map(d => d.equity));
  const sharpeRatio = 1.85; // Simulated
  const calmarRatio = 2.34; // Simulated

  // Custom tooltip
  interface CustomTooltipProps {
    active?: boolean;
    payload?: any[];
    label?: string;
  }

  const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 rounded-lg shadow-xl border border-gray-200">
          <p className="text-sm font-medium text-gray-600 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-2 mb-1">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              ></div>
              <span className="text-sm font-medium">
                {entry.name === 'equity' ? 'Equity' : 
                 entry.name === 'benchmark' ? 'S&P 500' : 'Drawdown'}:
              </span>
              <span className="text-sm font-bold">
                {entry.name === 'drawdown' ? 
                  `${entry.value.toFixed(2)}%` : 
                  `$${entry.value.toLocaleString()}`
                }
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  // Gradient definitions
  const gradientOffset = () => {
    const dataMax = Math.max(...equityData.map(d => d.equity));
    const dataMin = Math.min(...equityData.map(d => d.equity));
    if (dataMax <= 0) return 0;
    if (dataMin >= 0) return 1;
    return dataMax / (dataMax - dataMin);
  };

  const off = gradientOffset();

  return (
    <div className={`bg-white rounded-xl shadow-lg border border-gray-200 ${isFullscreen ? 'fixed inset-4 z-50' : 'p-6'}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6 p-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-800">Equity Curve</h3>
            <p className="text-sm text-gray-500">Rendimiento de la cuenta en tiempo real</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Timeframe Selector */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            {['1D', '1W', '1M', '3M'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${
                  timeframe === tf 
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
          
          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowDrawdown(!showDrawdown)}
              className={`p-2 rounded-lg transition-colors ${
                showDrawdown ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-400'
              }`}
              title="Toggle Drawdown"
            >
              <TrendingDown className="w-4 h-4" />
            </button>
            
            <button
              onClick={() => setShowBenchmark(!showBenchmark)}
              className={`p-2 rounded-lg transition-colors ${
                showBenchmark ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'
              }`}
              title="Toggle S&P 500"
            >
              <Target className="w-4 h-4" />
            </button>
            
            <button className="p-2 rounded-lg bg-gray-100 text-gray-400 hover:text-gray-600">
              <RefreshCw className="w-4 h-4" />
            </button>
            
            <button className="p-2 rounded-lg bg-gray-100 text-gray-400 hover:text-gray-600">
              <Download className="w-4 h-4" />
            </button>
            
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 rounded-lg bg-gray-100 text-gray-400 hover:text-gray-600"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Métricas principales */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 px-6">
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">Equity Actual</span>
          </div>
          <div className="text-2xl font-bold text-green-700">
            ${currentEquity.toLocaleString()}
          </div>
          <div className="text-sm text-green-600">
            +${(currentEquity - initialEquity).toLocaleString()}
          </div>
        </div>

        <div className={`rounded-lg p-4 ${totalReturn >= 0 ? 'bg-gradient-to-br from-blue-50 to-blue-100' : 'bg-gradient-to-br from-red-50 to-red-100'}`}>
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className={`w-4 h-4 ${totalReturn >= 0 ? 'text-blue-600' : 'text-red-600'}`} />
            <span className={`text-sm font-medium ${totalReturn >= 0 ? 'text-blue-800' : 'text-red-800'}`}>
              Retorno Total
            </span>
          </div>
          <div className={`text-2xl font-bold ${totalReturn >= 0 ? 'text-blue-700' : 'text-red-700'}`}>
            {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
          </div>
          <div className={`text-sm ${totalReturn >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
            Desde inicio
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-800">Max Drawdown</span>
          </div>
          <div className="text-2xl font-bold text-purple-700">
            {maxDrawdown.toFixed(2)}%
          </div>
          <div className="text-sm text-purple-600">
            Pérdida máxima
          </div>
        </div>

        <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="w-4 h-4 text-amber-600" />
            <span className="text-sm font-medium text-amber-800">Sharpe Ratio</span>
          </div>
          <div className="text-2xl font-bold text-amber-700">
            {sharpeRatio.toFixed(2)}
          </div>
          <div className="text-sm text-amber-600">
            Risk-adjusted
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="px-6 mb-4">
        <ResponsiveContainer width="100%" height={isFullscreen ? 500 : 400}>
          <AreaChart data={equityData}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset={off} stopColor="#3B82F6" stopOpacity={0.3}/>
                <stop offset={off} stopColor="#EF4444" stopOpacity={0.3}/>
              </linearGradient>
              <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#EF4444" stopOpacity={0.8}/>
                <stop offset="100%" stopColor="#EF4444" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis 
              dataKey="time" 
              stroke="#6B7280"
              fontSize={12}
              tickLine={false}
            />
            <YAxis 
              stroke="#6B7280"
              fontSize={12}
              tickLine={false}
              domain={['dataMin - 100', 'dataMax + 100']}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Línea de equity inicial */}
            <ReferenceLine 
              y={initialEquity} 
              stroke="#6B7280" 
              strokeDasharray="5 5" 
              label={{ value: "Capital Inicial", position: "left" }}
            />
            
            {/* Área de equity */}
            <Area
              type="monotone"
              dataKey="equity"
              stroke="#3B82F6"
              strokeWidth={3}
              fill="url(#equityGradient)"
              fillOpacity={0.6}
              animationDuration={2000}
            />
            
            {/* Benchmark si está habilitado */}
            {showBenchmark && (
              <Line
                type="monotone"
                dataKey="benchmark"
                stroke="#9CA3AF"
                strokeWidth={2}
                strokeDasharray="8 4"
                dot={false}
                animationDuration={2000}
              />
            )}
            
            {/* Drawdown si está habilitado */}
            {showDrawdown && (
              <Area
                type="monotone"
                dataKey="drawdown"
                stroke="#EF4444"
                strokeWidth={2}
                fill="url(#drawdownGradient)"
                fillOpacity={0.3}
                yAxisId="drawdown"
                animationDuration={2000}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer con estadísticas adicionales */}
      <div className="border-t border-gray-200 pt-4 px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-sm text-gray-500">Calmar Ratio</div>
            <div className="text-lg font-bold text-gray-800">{calmarRatio}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Win Rate</div>
            <div className="text-lg font-bold text-green-600">68.5%</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Volatilidad</div>
            <div className="text-lg font-bold text-blue-600">12.3%</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Max Equity</div>
            <div className="text-lg font-bold text-purple-600">${maxEquity.toLocaleString()}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EquityCurvePro;