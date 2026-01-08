import { useEffect, useState } from 'react';

export default function WorldClock({ className = '' }) {
  const [worldTime, setWorldTime] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorldTime();
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
      <div className={`panel ${className}`} style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
        Carregando tempo...
      </div>
    );
  }

  const { day, month, year, hour, minute, time_of_day, season } = worldTime;
  
  const timeIcon = {
    'dawn': '🌅', 'morning': '☀️', 'noon': '🌞', 'afternoon': '🌤️',
    'dusk': '🌇', 'evening': '🌆', 'night': '🌙', 'midnight': '🌑'
  }[time_of_day] || '⏰';

  const seasonIcon = {
    'Spring': '🌸', 'Summer': '☀️', 'Autumn': '🍂', 'Winter': '❄️'
  }[season] || '🌍';

  return (
    <div className={`flex items-center gap-md ${className}`}>
      {/* Time */}
      <div className="panel flex items-center gap-sm" style={{ padding: 'var(--spacing-sm) var(--spacing-md)' }}>
        <span style={{ fontSize: '1.25rem' }}>{timeIcon}</span>
        <span className="glow-gold" style={{ fontSize: '0.875rem', fontWeight: '500' }}>
          {String(hour).padStart(2, '0')}:{String(minute).padStart(2, '0')}
        </span>
      </div>

      {/* Date */}
      <div className="panel flex items-center gap-sm" style={{ padding: 'var(--spacing-sm) var(--spacing-md)' }}>
        <span style={{ fontSize: '1.25rem' }}>{seasonIcon}</span>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          {day}/{month}/{year}
        </span>
      </div>

      {/* Period Name */}
      <div className="badge badge-gold" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {time_of_day}
      </div>
    </div>
  );
}
