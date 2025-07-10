import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

interface WinRateProps {
  winRate?: number;
  totalTrades?: number;
}
const WinRateSpeedometer: React.FC<WinRateProps> = ({ winRate = 68.5, totalTrades = 250 }) => {
  const [animatedRate, setAnimatedRate] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedRate(winRate);
    }, 500);
    return () => clearTimeout(timer);
  }, [winRate]);

  // Calcular el ángulo para la aguja (0-180 grados)
  const angle = (animatedRate / 100) * 180;
  
  // Calcular el color basado en el win rate
  const getColor = (rate: number): string => {
    if (rate >= 80) return '#10B981'; // Verde
    if (rate >= 70) return '#F59E0B'; // Amarillo
    if (rate >= 60) return '#F97316'; // Naranja
    return '#EF4444'; // Rojo
  };

  const getGradientColor = (rate: number): string => {
    if (rate >= 80) return 'from-green-400 to-green-600';
    if (rate >= 70) return 'from-yellow-400 to-yellow-600';
    if (rate >= 60) return 'from-orange-400 to-orange-600';
    return 'from-red-400 to-red-600';
  };

  const getPerformanceText = (rate: number): string => {
    if (rate >= 80) return 'Excelente';
    if (rate >= 70) return 'Bueno';
    if (rate >= 60) return 'Regular';
    return 'Necesita Mejora';
  };

  // Crear las marcas del velocímetro
  const createTicks = () => {
    const ticks = [];
    for (let i = 0; i <= 10; i++) {
      const tickAngle = (i / 10) * 180;
      const isMainTick = i % 2 === 0;
      const tickLength = isMainTick ? 12 : 6;
      const tickWidth = isMainTick ? 2 : 1;
      
      const x1 = 150 + (120 - tickLength) * Math.cos((tickAngle - 90) * Math.PI / 180);
      const y1 = 150 + (120 - tickLength) * Math.sin((tickAngle - 90) * Math.PI / 180);
      const x2 = 150 + 120 * Math.cos((tickAngle - 90) * Math.PI / 180);
      const y2 = 150 + 120 * Math.sin((tickAngle - 90) * Math.PI / 180);
      
      ticks.push(
        <line
          key={i}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="#6B7280"
          strokeWidth={tickWidth}
        />
      );
      
      // Agregar etiquetas para las marcas principales
      if (isMainTick) {
        const labelX = 150 + 100 * Math.cos((tickAngle - 90) * Math.PI / 180);
        const labelY = 150 + 100 * Math.sin((tickAngle - 90) * Math.PI / 180);
        
        ticks.push(
          <text
            key={`label-${i}`}
            x={labelX}
            y={labelY}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="12"
            fill="#6B7280"
            fontWeight="500"
          >
            {i * 10}
          </text>
        );
      }
    }
    return ticks;
  };

  // Posición de la aguja
  const needleX = 150 + 80 * Math.cos((angle - 90) * Math.PI / 180);
  const needleY = 150 + 80 * Math.sin((angle - 90) * Math.PI / 180);

  return (
    <div className="flex flex-col items-center p-6 bg-white rounded-xl shadow-lg border border-gray-200 max-w-md mx-auto">
      {/* Header */}
      <div className="text-center mb-4">
        <div className="flex items-center justify-center gap-2 mb-2">
          <BarChart3 className="w-6 h-6 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-800">Win Rate</h3>
        </div>
        <p className="text-sm text-gray-500">Rendimiento General</p>
      </div>

      {/* Speedometer */}
      <div className="relative">
        <svg width="300" height="200" viewBox="0 0 300 200">
          {/* Arco de fondo */}
          <path
            d="M 30 150 A 120 120 0 0 1 270 150"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="20"
            strokeLinecap="round"
          />
          
          {/* Arco de progreso */}
          <path
            d="M 30 150 A 120 120 0 0 1 270 150"
            fill="none"
            stroke={getColor(animatedRate)}
            strokeWidth="20"
            strokeLinecap="round"
            strokeDasharray={`${(animatedRate / 100) * 377} 377`}
            className="transition-all duration-2000 ease-out"
          />
          
          {/* Marcas del velocímetro */}
          {createTicks()}
          
          {/* Aguja */}
          <line
            x1="150"
            y1="150"
            x2={needleX}
            y2={needleY}
            stroke="#1F2937"
            strokeWidth="3"
            strokeLinecap="round"
            className="transition-all duration-2000 ease-out"
          />
          
          {/* Centro de la aguja */}
          <circle
            cx="150"
            cy="150"
            r="8"
            fill="#1F2937"
          />
          <circle
            cx="150"
            cy="150"
            r="4"
            fill="#FFFFFF"
          />
          
          {/* Zonas de color de fondo */}
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#EF4444" />
              <stop offset="33%" stopColor="#F97316" />
              <stop offset="66%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#10B981" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Información del Win Rate */}
      <div className="text-center mt-4 space-y-2">
        <div className="flex items-center justify-center gap-2">
          <span className={`text-4xl font-bold bg-gradient-to-r ${getGradientColor(animatedRate)} bg-clip-text text-transparent`}>
            {animatedRate.toFixed(1)}%
          </span>
          {animatedRate >= 70 ? (
            <TrendingUp className="w-6 h-6 text-green-500" />
          ) : (
            <TrendingDown className="w-6 h-6 text-red-500" />
          )}
        </div>
        
        <div className="flex items-center justify-center gap-4 text-sm text-gray-600">
          <span className={`px-3 py-1 rounded-full font-medium ${
            animatedRate >= 80 ? 'bg-green-100 text-green-800' :
            animatedRate >= 70 ? 'bg-yellow-100 text-yellow-800' :
            animatedRate >= 60 ? 'bg-orange-100 text-orange-800' :
            'bg-red-100 text-red-800'
          }`}>
            {getPerformanceText(animatedRate)}
          </span>
        </div>
        
        <div className="text-xs text-gray-500">
          Basado en {totalTrades.toLocaleString()} trades
        </div>
      </div>

      {/* Estadísticas adicionales */}
      <div className="grid grid-cols-2 gap-4 mt-6 w-full">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {Math.round((animatedRate / 100) * totalTrades)}
          </div>
          <div className="text-xs text-gray-600">Trades Ganados</div>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-red-600">
            {Math.round(((100 - animatedRate) / 100) * totalTrades)}
          </div>
          <div className="text-xs text-gray-600">Trades Perdidos</div>
        </div>
      </div>
    </div>
  );
};

export default WinRateSpeedometer;