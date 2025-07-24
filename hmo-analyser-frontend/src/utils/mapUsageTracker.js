class MapUsageTracker {
  constructor() {
    this.sessionId = this.generateSessionId();
    this.startTime = Date.now();
    this.events = [];
    this.apiEndpoint = '/api/map-usage'; // Your backend endpoint
  }

  generateSessionId() {
    return `map_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Track different types of map events
  trackMapLoad(styleUrl, loadTime = null) {
    const event = {
      type: 'map_load',
      sessionId: this.sessionId,
      timestamp: Date.now(),
      data: {
        style: this.getStyleName(styleUrl),
        loadTime: loadTime,
        userAgent: navigator.userAgent,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      }
    };
    
    this.events.push(event);
    this.sendEvent(event);
    console.log('📊 Map Load Tracked:', event);
  }

  trackStyleChange(oldStyle, newStyle) {
    const event = {
      type: 'style_change', // This counts as a new map load!
      sessionId: this.sessionId,
      timestamp: Date.now(),
      data: {
        from: this.getStyleName(oldStyle),
        to: this.getStyleName(newStyle)
      }
    };
    
    this.events.push(event);
    this.sendEvent(event);
    console.log('🎨 Style Change Tracked (NEW MAP LOAD):', event);
  }

  trackFilterUsage(filterType, value, resultCount) {
    const event = {
      type: 'filter_usage',
      sessionId: this.sessionId,
      timestamp: Date.now(),
      data: {
        filterType,
        value,
        resultCount,
        duration: Date.now() - this.startTime
      }
    };
    
    this.events.push(event);
    // Don't send immediately for filters (batch them)
    console.log('🔍 Filter Usage Tracked:', event);
  }

  trackPropertyInteraction(propertyId, interactionType) {
    const event = {
      type: 'property_interaction',
      sessionId: this.sessionId,
      timestamp: Date.now(),
      data: {
        propertyId,
        interactionType, // 'marker_click', 'popup_view', 'details_link'
        duration: Date.now() - this.startTime
      }
    };
    
    this.events.push(event);
    console.log('🏠 Property Interaction Tracked:', event);
  }

  trackSessionEnd() {
    const sessionDuration = Date.now() - this.startTime;
    const event = {
      type: 'session_end',
      sessionId: this.sessionId,
      timestamp: Date.now(),
      data: {
        duration: sessionDuration,
        totalEvents: this.events.length,
        mapLoads: this.events.filter(e => e.type === 'map_load' || e.type === 'style_change').length,
        propertyInteractions: this.events.filter(e => e.type === 'property_interaction').length,
        filterUsage: this.events.filter(e => e.type === 'filter_usage').length
      }
    };
    
    this.events.push(event);
    this.sendBatchEvents(); // Send all remaining events
    console.log('📈 Session End Tracked:', event);
  }

  getStyleName(styleUrl) {
    const styleMap = {
      'mapbox://styles/mapbox/streets-v12': 'Streets',
      'mapbox://styles/mapbox/satellite-streets-v12': 'Satellite',
      'mapbox://styles/mapbox/light-v11': 'Light',
      'mapbox://styles/mapbox/dark-v11': 'Dark',
      'mapbox://styles/mapbox/outdoors-v12': 'Outdoors'
    };
    return styleMap[styleUrl] || 'Unknown';
  }

  // Send individual event to backend
  async sendEvent(event) {
    try {
      await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event)
      });
    } catch (error) {
      console.warn('Failed to send usage event:', error);
      // Store in localStorage as backup
      this.storeEventLocally(event);
    }
  }

  // Send multiple events in batch
  async sendBatchEvents() {
    const unsent = this.events.filter(e => !e.sent);
    if (unsent.length === 0) return;

    try {
      await fetch(`${this.apiEndpoint}/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ events: unsent })
      });
      
      // Mark events as sent
      unsent.forEach(event => event.sent = true);
    } catch (error) {
      console.warn('Failed to send batch events:', error);
      unsent.forEach(event => this.storeEventLocally(event));
    }
  }

  // Backup storage for offline/failed requests
  storeEventLocally(event) {
    const stored = JSON.parse(localStorage.getItem('mapUsageEvents') || '[]');
    stored.push(event);
    localStorage.setItem('mapUsageEvents', JSON.stringify(stored.slice(-100))); // Keep last 100
  }

  // Get usage statistics for display
  getSessionStats() {
    const mapLoads = this.events.filter(e => e.type === 'map_load' || e.type === 'style_change').length;
    const interactions = this.events.filter(e => e.type === 'property_interaction').length;
    const filters = this.events.filter(e => e.type === 'filter_usage').length;
    const duration = Date.now() - this.startTime;

    return {
      sessionId: this.sessionId,
      duration: Math.round(duration / 1000), // seconds
      mapLoads,
      interactions,
      filters,
      totalEvents: this.events.length
    };
  }
}

export default MapUsageTracker;