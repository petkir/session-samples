import { appInsights } from '../appInsights';

class PositionTrackingService {
  private watchId: number | null = null;
  private trackingInterval: number | null = null;

  

  public startTracking(interval: number = 30000) {
    if ('geolocation' in navigator) {
      this.watchId = navigator.geolocation.watchPosition(
        this.handlePosition.bind(this),
        this.handleError.bind(this),
        { enableHighAccuracy: true }
      );

      this.trackingInterval = window.setInterval(() => {
        if (this.watchId !== null) {
          navigator.geolocation.getCurrentPosition(()=>{console.log("got it")},()=>{console.log("error")});
        }
      }, interval);
    } else {
      console.error('Geolocation is not supported by this browser.');
    }
  }

  public stopTracking() {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }

    if (this.trackingInterval !== null) {
      clearInterval(this.trackingInterval);
      this.trackingInterval = null;
    }
  }

  private handlePosition(position: GeolocationPosition) {
    const { latitude, longitude } = position.coords;
    appInsights.trackEvent({
      name: 'UserPosition',
      properties: {
        latitude,
        longitude,
        timestamp: new Date().toISOString(),
      },
    });
  }

  private handleError(error: GeolocationPositionError) {
    console.error(`Geolocation error: ${error.message}`);
  }
}

export const positionTrackingService = new PositionTrackingService();
