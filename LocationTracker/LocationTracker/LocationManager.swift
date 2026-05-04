import CoreLocation
import Combine

class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()

    @Published var location: CLLocation?
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined
    @Published var isRecording = false
    @Published var recordedLocations: [CLLocation] = []

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.distanceFilter = 5
        authorizationStatus = manager.authorizationStatus
    }

    func requestPermission() {
        manager.requestWhenInUseAuthorization()
    }

    func startRecording() {
        recordedLocations = []
        isRecording = true
        manager.startUpdatingLocation()
    }

    func stopRecording() {
        isRecording = false
        manager.stopUpdatingLocation()
    }

    func clearTrack() {
        recordedLocations = []
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let newLocation = locations.last else { return }
        self.location = newLocation
        if isRecording {
            recordedLocations.append(newLocation)
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus
        if manager.authorizationStatus == .authorizedWhenInUse ||
           manager.authorizationStatus == .authorizedAlways {
            manager.startUpdatingLocation()
        }
    }

    var totalDistance: CLLocationDistance {
        let locs = recordedLocations
        guard locs.count > 1 else { return 0 }
        return zip(locs, locs.dropFirst()).reduce(0) { $0 + $1.1.distance(from: $1.0) }
    }
}
