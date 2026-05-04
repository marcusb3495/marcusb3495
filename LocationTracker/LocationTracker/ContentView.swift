import SwiftUI
import MapKit

struct ContentView: View {
    @StateObject private var locationManager = LocationManager()

    var body: some View {
        ZStack(alignment: .bottom) {
            MapView(locationManager: locationManager)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                if !locationManager.recordedLocations.isEmpty {
                    StatsBar(locationManager: locationManager)
                }
                ControlBar(locationManager: locationManager)
            }
        }
        .onAppear {
            locationManager.requestPermission()
        }
        .alert("Location Access Required", isPresented: .constant(
            locationManager.authorizationStatus == .denied ||
            locationManager.authorizationStatus == .restricted
        )) {
            Button("Open Settings") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Enable location access in Settings to record your path.")
        }
    }
}

struct StatsBar: View {
    @ObservedObject var locationManager: LocationManager

    var body: some View {
        HStack {
            StatCell(label: "Points", value: "\(locationManager.recordedLocations.count)")
            Spacer()
            StatCell(label: "Distance", value: formattedDistance(locationManager.totalDistance), alignment: .trailing)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial)
    }

    private func formattedDistance(_ meters: Double) -> String {
        meters < 1000
            ? String(format: "%.0f m", meters)
            : String(format: "%.2f km", meters / 1000)
    }
}

struct StatCell: View {
    let label: String
    let value: String
    var alignment: HorizontalAlignment = .leading

    var body: some View {
        VStack(alignment: alignment, spacing: 2) {
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value)
                .font(.headline)
                .monospacedDigit()
        }
    }
}

struct ControlBar: View {
    @ObservedObject var locationManager: LocationManager

    var body: some View {
        HStack(spacing: 12) {
            if locationManager.isRecording {
                ActionButton(title: "Stop Recording", icon: "stop.circle.fill", color: .red) {
                    locationManager.stopRecording()
                }
            } else {
                ActionButton(title: "Start Recording", icon: "record.circle", color: .blue) {
                    locationManager.startRecording()
                }
                if !locationManager.recordedLocations.isEmpty {
                    ActionButton(title: "Clear", icon: "trash", color: .orange) {
                        locationManager.clearTrack()
                    }
                    .frame(maxWidth: 120)
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial)
    }
}

struct ActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Label(title, systemImage: icon)
                .font(.headline)
                .foregroundColor(.white)
                .padding(.vertical, 14)
                .frame(maxWidth: .infinity)
                .background(color)
                .cornerRadius(12)
        }
    }
}
