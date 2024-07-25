import { appInsights } from '../appInsights';

class PositionTrackingService {
  private watchId: number | null = null;
  private trackingInterval: number | null = null;



  public startTracking(interval: number = 30000) {
    if ('geolocation' in navigator) {
      this.watchId = navigator.geolocation.watchPosition(
        this.handlePosition.bind(this),
        this.handleError.bind(this),
        { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 }
      );


    } else {
      console.error('Geolocation is not supported by this browser.');
    }
  }

  public getCurrentPosition() {
    return new Promise<GeolocationPosition>((resolve, reject) => {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition((pos) => {

          const crd = pos.coords;

          console.log("Your current position is:");
          console.log(`Latitude : ${crd.latitude}`);
          console.log(`Longitude: ${crd.longitude}`);
          console.log(`More or less ${crd.accuracy} meters.`);
          resolve(pos);
        }, (err) => {
          console.warn(`ERROR(${err.code}): ${err.message}`);
          reject(err);
        });
      } else {
        reject(new Error('Geolocation is not supported by this browser.'));
      }
    });
  }

  public stopTracking() {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
  }

  private handlePosition(position: GeolocationPosition) {
    const { latitude, longitude } = position.coords;
    window.localStorage.setItem('position', JSON.stringify(position));
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
