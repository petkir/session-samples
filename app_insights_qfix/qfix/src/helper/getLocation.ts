export function getLocation(): Promise<{ latitude: number, longitude: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject('Geolocation is not supported by this browser.');
    } else {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
        },
        (error) => {
          reject('Error getting location: ' + error.message);
        }
      );
    }
  });
}