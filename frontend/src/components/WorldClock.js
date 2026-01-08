import { useEffect, useState } from 'react';

export default function WorldClock({ className = '' }) {
  const [worldTime, setWorldTime] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorldTime();
    // Poll every 30 seconds to keep time updated
    const interval = setInterval(fetchWorldTime, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchWorldTime = async () => {
    try {
      const response = await fetch('http://localhost:8000/world/time');
      const data = await response.json();
      setWorldTime(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch world time:', error);
      setLoading(false);
    }
  };

  if (loading || !worldTime) {
    return (
      <div className={`text-sm text-secondary ${className}`}>
        Carregando tempo...
      </div>
    );
  }

  const { day, month, year, hour, minute, time_of_day, season } = worldTime;
  
  // Time of day icon
  const timeIcon = {
    'dawn': '🌅',
    'morning': '☀️',
    'noon': '🌞',
    'afternoon': '🌤️',
    'dusk': '🌇',
    'evening': '🌆',
    'night': '🌙',
    'midnight': '🌑'
  }[time_of_day] || '⏰';

  // Season icon
  const seasonIcon = {
    'Spring': '🌸',
    'Summer': '☀️',
    'Autumn': '🍂',
    'Winter': '❄️'
  }[season] || '🌍';

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Time */}
      <div className="flex items-center gap-1 bg-black/30 px-3 py-1.5 rounded-lg">
        <span className="text-xl">{timeIcon}</span>
        <span className="text-sm font-medium text-gold">
          {String(hour).padStart(2, '0')}:{String(minute).padStart(2, '0')}
        </span>
      </div>

      {/* Date */}
      <div className="flex items-center gap-1 bg-black/30 px-3 py-1.5 rounded-lg">
        <span className="text-xl">{seasonIcon}</span>
        <span className="text-sm text-secondary">
          {day}/{month}/{year}
        </span>
      </div>

      {/* Period Name */}
      <div className="bg-black/20 px-3 py-1.5 rounded-lg">
        <span className="text-xs uppercase tracking-wider text-gold/70">
          {time_of_day}
        </span>
      </div>
    </div>
  );
}
