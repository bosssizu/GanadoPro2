import SwiftUI
import ARKit

struct ContentView: View {
    @StateObject private var capture = DepthCaptureManager()
    @State private var isScanning = false
    @State private var seconds: Int = 0
    @State private var status: String = "Listo para escanear"
    @State private var exportURL: URL?
    @State private var uploadOK: Bool? = nil
    @State private var sid: String = UUID().uuidString
    @State private var category: String = "engorde" // ajustar si usas otra

    var body: some View {
        VStack(spacing: 12) {
            Text("GanadoBravo Scan (iOS) – MVP").font(.headline)
            HStack {
                Label(capture.deviceHasDepth ? "LiDAR / SceneDepth OK" : "Sin LiDAR: modo básico", systemImage: capture.deviceHasDepth ? "light.min" : "camera")
                    .foregroundColor(capture.deviceHasDepth ? .green : .orange)
                Spacer()
            }
            ZStack {
                ARPreviewView(session: capture.session).overlay(alignment: .topLeading) {
                    Text("t=\(seconds)s · kf=\(capture.keyframes.count)")
                        .padding(6).background(.black.opacity(0.6)).foregroundColor(.white).clipShape(RoundedRectangle(cornerRadius: 8))
                        .padding(8)
                }.frame(height: 320).clipShape(RoundedRectangle(cornerRadius: 12))
            }

            Text(status).font(.subheadline).foregroundColor(.secondary)

            HStack {
                Button {
                    if isScanning { stopScan() } else { startScan() }
                } label: {
                    Text(isScanning ? "Detener (\(seconds)s)" : "Iniciar escaneo (\(Int(Config.minSeconds))–\(Int(Config.maxSeconds)) s)")
                        .font(.system(size: 18, weight: .bold))
                        .frame(maxWidth: .infinity).padding().background(isScanning ? Color.red : Color.blue).foregroundColor(.white).clipShape(RoundedRectangle(cornerRadius: 14))
                }
            }

            if let exportURL {
                HStack {
                    Button {
                        uploadPLY(url: exportURL)
                    } label: {
                        Text("Subir a GanadoBravo").font(.system(size: 16, weight: .bold))
                            .frame(maxWidth: .infinity).padding().background(Color.green).foregroundColor(.white).clipShape(RoundedRectangle(cornerRadius: 14))
                    }
                    Link("Ver archivo", destination: exportURL).buttonStyle(.borderedProminent)
                }
            }

            if let uploadOK {
                Text(uploadOK ? "Subida OK" : "Error de subida").foregroundColor(uploadOK ? .green : .red)
            }

            Spacer(minLength: 10)
            HStack {
                Text("Keyframes: \(capture.keyframes.count)").font(.footnote)
                Spacer()
                Text("HasDepth: \(capture.deviceHasDepth.description)").font(.footnote)
            }
        }
        .padding()
        .onAppear { capture.configureSession() }
    }

    private func startScan() {
        status = "Escaneando… Muévete 180–270° alrededor del animal."
        seconds = 0; isScanning = true; exportURL = nil; uploadOK = nil
        capture.start()
        // simple timer 1 Hz
        Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { t in
            guard isScanning else { t.invalidate(); return }
            seconds += 1
            if seconds >= Int(Config.maxSeconds) {
                stopScan()
            }
        }
    }

    private func stopScan() {
        isScanning = false; capture.stop()
        status = "Procesando…"
        DispatchQueue.global(qos: .userInitiated).async {
            let cloud = PointCloudFusion.fuse(keyframes: capture.keyframes, voxel: 0.01, minNeighbors: 8, radius: 0.05)
            let tmp = FileManager.default.temporaryDirectory.appendingPathComponent("scan_\(UUID().uuidString).ply")
            do {
                try PLYWriter.writeASCII(points: cloud, to: tmp)
                DispatchQueue.main.async {
                    self.exportURL = tmp
                    self.status = "Listo. Exportado PLY (\(cloud.count) pts)."
                }
            } catch {
                DispatchQueue.main.async { self.status = "Error exportando PLY: \(error.localizedDescription)" }
            }
        }
    }

    private func uploadPLY(url: URL) {
        status = "Subiendo…"
        let meta = UploadMeta(
            sid: sid, category: category, durationSec: Double(seconds),
            keyframes: capture.keyframes.count, deviceModel: UIDevice.current.name,
            hasDepth: capture.deviceHasDepth
        )
        Uploader.uploadPLY(fileURL: url, meta: meta, to: Config.uploadURL) { ok, err in
            DispatchQueue.main.async {
                self.uploadOK = ok
                self.status = ok ? "Subida OK" : "Error de subida: \(err ?? "?")"
            }
        }
    }
}

struct ARPreviewView: UIViewRepresentable {
    let session: ARSession
    func makeUIView(context: Context) -> ARSCNView {
        let v = ARSCNView(frame: .zero)
        v.session = session
        v.automaticallyUpdatesLighting = true
        v.scene = SCNScene()
        return v
    }
    func updateUIView(_ uiView: ARSCNView, context: Context) {}
}
