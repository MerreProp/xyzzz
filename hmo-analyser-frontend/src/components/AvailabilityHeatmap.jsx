import React, { useState, useEffect } from 'react';

const AvailabilityHeatmap = ({ propertyId }) => {
  const [heatmapData, setHeatmapData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(null);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [viewMode, setViewMode] = useState('monthly'); // 'monthly', 'quarterly', 'yearly'

  // ADD THIS useEffect HOOK
  useEffect(() => {
    fetchHeatmapData();
  }, [propertyId, currentMonth, viewMode]);

  const fetchHeatmapData = async () => {
    if (!propertyId) return;
    
    setIsLoading(true);
    try {
      const startDate = getStartDate();
      const endDate = getEndDate();
      
      console.log(`Fetching heatmap data for ${propertyId} from ${startDate} to ${endDate}`);
      
      const response = await fetch(
        `/api/properties/${propertyId}/availability-calendar?start_date=${startDate}&end_date=${endDate}`
      );
      
      if (response.ok) {
        const data = await response.json();
        console.log('Real API data received:', data);
        setHeatmapData(data);
      } else {
        console.error('API endpoint not available, status:', response.status);
        // Show a message instead of fake data
        setHeatmapData({
          error: true,
          message: 'Calendar data not available yet. Please implement the API endpoint.',
          calendar_data: {},
          room_summary: {
            total_rooms: 0,
            avg_occupancy_rate: 0
          }
        });
      }
    } catch (error) {
      console.error('Error fetching heatmap data:', error);
      // Show error message instead of fake data
      setHeatmapData({
        error: true,
        message: 'Unable to load calendar data. Check if the API endpoint is implemented.',
        calendar_data: {},
        room_summary: {
          total_rooms: 0,
          avg_occupancy_rate: 0
        }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStartDate = () => {
    const date = new Date(currentMonth);
    if (viewMode === 'monthly') {
      date.setDate(1);
    } else if (viewMode === 'quarterly') {
      date.setMonth(date.getMonth() - 2);
      date.setDate(1);
    } else if (viewMode === 'yearly') {
      date.setMonth(0);
      date.setDate(1);
    }
    return date.toISOString().split('T')[0];
  };

  const getEndDate = () => {
    const date = new Date(currentMonth);
    if (viewMode === 'monthly') {
      date.setMonth(date.getMonth() + 1);
      date.setDate(0);
    } else if (viewMode === 'quarterly') {
      date.setMonth(date.getMonth() + 1);
      date.setDate(0);
    } else if (viewMode === 'yearly') {
      date.setMonth(11);
      date.setDate(31);
    }
    return date.toISOString().split('T')[0];
  };

  // REMOVE THIS FUNCTION - DELETE IT ENTIRELY
  // const generateSampleData = () => { ... }

  const getIntensityColor = (occupancyRate) => {
    if (occupancyRate >= 90) return '#0f5132'; // Dark green - almost full
    if (occupancyRate >= 70) return '#198754'; // Green - high occupancy
    if (occupancyRate >= 50) return '#ffc107'; // Yellow - medium occupancy
    if (occupancyRate >= 25) return '#fd7e14'; // Orange - low occupancy
    if (occupancyRate > 0) return '#dc3545'; // Red - very low occupancy
    return '#e9ecef'; // Light gray - empty
  };

  const renderCalendarGrid = () => {
    if (!heatmapData?.calendar_data || Object.keys(heatmapData.calendar_data).length === 0) {
      return (
        <div style={{ 
          textAlign: 'center', 
          padding: '2rem',
          backgroundColor: '#f8fafc',
          borderRadius: '8px',
          border: '1px dashed #cbd5e1'
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📅</div>
          <p style={{ color: '#64748b' }}>No calendar data available for this time period</p>
        </div>
      );
    }

    const calendarData = heatmapData.calendar_data;
    const dates = Object.keys(calendarData).sort();
    
    if (viewMode === 'monthly') {
      return renderMonthlyGrid(dates, calendarData);
    } else {
      return renderTimelineGrid(dates, calendarData);
    }
  };

  const renderMonthlyGrid = (dates, calendarData) => {
    if (dates.length === 0) return null;
    
    // Create a traditional calendar grid
    const firstDate = new Date(dates[0]);
    const lastDate = new Date(dates[dates.length - 1]);
    const startOfCalendar = new Date(firstDate);
    startOfCalendar.setDate(1);
    
    // Get to the first Sunday before the first day of the month
    while (startOfCalendar.getDay() !== 0) {
      startOfCalendar.setDate(startOfCalendar.getDate() - 1);
    }

    const weeks = [];
    let currentWeek = [];
    let currentDate = new Date(startOfCalendar);

    // Generate 6 weeks to ensure we cover the whole month
    for (let week = 0; week < 6; week++) {
      currentWeek = [];
      for (let day = 0; day < 7; day++) {
        const dateStr = currentDate.toISOString().split('T')[0];
        const dayData = calendarData[dateStr];
        const isCurrentMonth = currentDate.getMonth() === firstDate.getMonth();
        
        currentWeek.push({
          date: new Date(currentDate),
          dateStr,
          dayData,
          isCurrentMonth
        });
        
        currentDate.setDate(currentDate.getDate() + 1);
      }
      weeks.push(currentWeek);
    }

    return (
      <div style={{ marginTop: '1rem' }}>
        {/* Weekday headers */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px', marginBottom: '0.5rem' }}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} style={{ 
              textAlign: 'center', 
              fontSize: '0.875rem', 
              fontWeight: '600',
              color: '#64748b',
              padding: '0.5rem'
            }}>
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(7, 1fr)', 
            gap: '2px',
            marginBottom: '2px'
          }}>
            {week.map((day, dayIndex) => (
              <div
                key={`${weekIndex}-${dayIndex}`}
                style={{
                  aspectRatio: '1',
                  backgroundColor: day.dayData ? getIntensityColor(day.dayData.occupancy_rate) : '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '4px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: day.dayData ? 'pointer' : 'default',
                  opacity: day.isCurrentMonth ? 1 : 0.3,
                  transition: 'all 0.2s ease',
                  position: 'relative'
                }}
                onClick={() => day.dayData && setSelectedDate(day.dateStr)}
                onMouseEnter={(e) => {
                  if (day.dayData) {
                    e.target.title = `${day.date.getDate()}: ${Math.round(day.dayData.occupancy_rate)}% occupied (${day.dayData.available_rooms}/${day.dayData.total_rooms} available)`;
                  }
                }}
              >
                <div style={{ 
                  fontSize: '0.875rem', 
                  fontWeight: day.dayData ? '600' : '400',
                  color: day.dayData && day.dayData.occupancy_rate > 50 ? 'white' : '#1e293b'
                }}>
                  {day.date.getDate()}
                </div>
                {day.dayData && (
                  <div style={{ 
                    fontSize: '0.625rem',
                    color: day.dayData.occupancy_rate > 50 ? 'white' : '#64748b',
                    marginTop: '2px'
                  }}>
                    {Math.round(day.dayData.occupancy_rate)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  };

  const renderTimelineGrid = (dates, calendarData) => {
    if (dates.length === 0) return null;
    
    // Render as a timeline for quarterly/yearly views
    const itemsPerRow = viewMode === 'quarterly' ? 30 : 26;
    const rows = [];
    
    for (let i = 0; i < dates.length; i += itemsPerRow) {
      rows.push(dates.slice(i, i + itemsPerRow));
    }

    return (
      <div style={{ marginTop: '1rem' }}>
        {rows.map((row, rowIndex) => (
          <div key={rowIndex} style={{ 
            display: 'flex', 
            gap: '2px',
            marginBottom: '4px',
            flexWrap: 'wrap'
          }}>
            {row.map(dateStr => {
              const dayData = calendarData[dateStr];
              const date = new Date(dateStr);
              
              return (
                <div
                  key={dateStr}
                  style={{
                    width: '12px',
                    height: '12px',
                    backgroundColor: getIntensityColor(dayData.occupancy_rate),
                    border: '1px solid #e2e8f0',
                    borderRadius: '2px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onClick={() => setSelectedDate(dateStr)}
                  title={`${date.toLocaleDateString('en-GB')}: ${Math.round(dayData.occupancy_rate)}% occupied`}
                />
              );
            })}
          </div>
        ))}
      </div>
    );
  };

  const navigateMonth = (direction) => {
    const newMonth = new Date(currentMonth);
    if (viewMode === 'monthly') {
      newMonth.setMonth(newMonth.getMonth() + direction);
    } else if (viewMode === 'quarterly') {
      newMonth.setMonth(newMonth.getMonth() + (direction * 3));
    } else if (viewMode === 'yearly') {
      newMonth.setFullYear(newMonth.getFullYear() + direction);
    }
    setCurrentMonth(newMonth);
  };

  const getDisplayTitle = () => {
    if (viewMode === 'monthly') {
      return currentMonth.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' });
    } else if (viewMode === 'quarterly') {
      const quarter = Math.floor(currentMonth.getMonth() / 3) + 1;
      return `Q${quarter} ${currentMonth.getFullYear()}`;
    } else {
      return currentMonth.getFullYear().toString();
    }
  };

  if (isLoading) {
    return (
      <div className="card">
        <h3 className="card-title">📅 Availability Calendar</h3>
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto' }}></div>
          <p style={{ marginTop: '1rem' }}>Loading calendar data...</p>
        </div>
      </div>
    );
  }

  // ADD THIS ERROR HANDLING
  if (heatmapData?.error) {
    return (
      <div className="card">
        <h3 className="card-title">📅 Availability Calendar Heatmap</h3>
        <div style={{ 
          textAlign: 'center', 
          padding: '3rem',
          backgroundColor: '#fef2f2',
          borderRadius: '8px',
          border: '1px solid #fecaca'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
          <h4 style={{ color: '#dc2626', marginBottom: '1rem' }}>Calendar Data Not Available</h4>
          <p style={{ color: '#991b1b', fontSize: '0.875rem', maxWidth: '500px', margin: '0 auto' }}>
            {heatmapData.message}
          </p>
          
          <div style={{ 
            marginTop: '2rem',
            padding: '1rem',
            backgroundColor: '#fef3c7',
            borderRadius: '6px',
            fontSize: '0.875rem'
          }}>
            <strong>To fix this:</strong>
            <ol style={{ marginTop: '0.5rem', paddingLeft: '1.5rem', textAlign: 'left' }}>
              <li>Make sure you've added the API endpoint to main.py</li>
              <li>Restart your FastAPI server: <code>python main.py</code></li>
              <li>Test the endpoint: <code>/api/properties/{propertyId}/availability-calendar?start_date=2024-01-01&end_date=2024-12-31</code></li>
              <li>Check your property has room availability periods in the database</li>
            </ol>
          </div>
          
          <div style={{ marginTop: '1rem' }}>
            <button 
              onClick={() => window.open(`/api/properties/${propertyId}/availability-calendar?start_date=2024-01-01&end_date=2024-12-31`, '_blank')}
              className="btn btn-secondary"
            >
              🔍 Test API Endpoint
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h3 className="card-title">📅 Availability Calendar Heatmap</h3>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {/* View Mode Selector */}
          <select 
            value={viewMode} 
            onChange={(e) => setViewMode(e.target.value)}
            style={{ 
              padding: '0.5rem', 
              border: '1px solid #e5e7eb', 
              borderRadius: '6px',
              fontSize: '0.875rem'
            }}
          >
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </select>
          
          {/* Navigation */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button 
              onClick={() => navigateMonth(-1)}
              style={{ 
                padding: '0.5rem',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                background: 'white',
                cursor: 'pointer'
              }}
            >
              ←
            </button>
            
            <div style={{ 
              minWidth: '150px', 
              textAlign: 'center',
              fontWeight: '600',
              fontSize: '1rem'
            }}>
              {getDisplayTitle()}
            </div>
            
            <button 
              onClick={() => navigateMonth(1)}
              style={{ 
                padding: '0.5rem',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                background: 'white',
                cursor: 'pointer'
              }}
            >
              →
            </button>
          </div>
        </div>
      </div>

      {/* Summary Statistics */}
      {heatmapData?.room_summary && heatmapData.room_summary.total_rooms > 0 && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
          gap: '1rem', 
          marginBottom: '2rem' 
        }}>
          <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#059669' }}>
              {heatmapData.room_summary.total_rooms}
            </div>
            <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Total Rooms</div>
          </div>
          
          <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#667eea' }}>
              {Math.round(heatmapData.room_summary.avg_occupancy_rate)}%
            </div>
            <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Avg Occupancy</div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '1rem', 
        marginBottom: '1rem',
        fontSize: '0.875rem',
        color: '#64748b'
      }}>
        <span>Occupancy:</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#e9ecef', border: '1px solid #dee2e6' }}></div>
          <span>0%</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#dc3545', border: '1px solid #dee2e6' }}></div>
          <span>25%</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#ffc107', border: '1px solid #dee2e6' }}></div>
          <span>50%</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#198754', border: '1px solid #dee2e6' }}></div>
          <span>75%</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#0f5132', border: '1px solid #dee2e6' }}></div>
          <span>90%+</span>
        </div>
      </div>

      {/* Calendar Display */}
      {renderCalendarGrid()}

      {/* Selected Date Details */}
      {selectedDate && heatmapData?.calendar_data[selectedDate] && (
        <div style={{ 
          marginTop: '2rem',
          padding: '1rem',
          backgroundColor: '#f8fafc',
          borderRadius: '8px',
          border: '1px solid #e2e8f0'
        }}>
          <h4 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem' }}>
            📊 {new Date(selectedDate).toLocaleDateString('en-GB', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </h4>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#059669' }}>
                {Math.round(heatmapData.calendar_data[selectedDate].occupancy_rate)}%
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Occupancy Rate</div>
            </div>
            
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#667eea' }}>
                {heatmapData.calendar_data[selectedDate].available_rooms}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Available Rooms</div>
            </div>
            
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#f59e0b' }}>
                {heatmapData.calendar_data[selectedDate].rooms_by_status.taken}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Taken Rooms</div>
            </div>
          </div>
        </div>
      )}

      {/* Usage Instructions */}
      <div style={{ 
        marginTop: '2rem',
        padding: '1rem',
        backgroundColor: '#fef3c7',
        borderRadius: '8px',
        fontSize: '0.875rem'
      }}>
        <strong>💡 How to use:</strong>
        <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
          <li>Hover over dates to see occupancy details</li>
          <li>Click dates to view detailed breakdown</li>
          <li>Use view modes: Monthly for detailed calendar, Quarterly/Yearly for trends</li>
          <li>Navigate using arrow buttons to explore different time periods</li>
        </ul>
      </div>
    </div>
  );
};

export default AvailabilityHeatmap;