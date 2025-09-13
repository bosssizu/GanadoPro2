import SwiftUI
import ARKit
import RealityKit
import simd
import Photos

final class PointCollector {
    var pts: [(Float,Float,Float)] = []
    func add(_ x: Float, _ y: Float, _ z: Float) { pts.append((x,y,z)) }
    func downsample(maxPoints: Int = 150_000) { if pts.count > maxPoints { let s = max(1, pts.count / maxPoints); pts = pts.enumerated().compactMap{ $0.offset % s == 0 ? $0.element : nil } } }
    func writePLY(to url: URL) throws {
        var txt = "ply\nformat ascii 1.0\n"
        txt += "element vertex \(pts.count)\nproperty float x\nproperty float y\nproperty float z\nend_header\n"
        for (x,y,z) in pts { txt += "\(x) \(y) \(z)\n" }
        try txt.write(to: url, atomically: true, encoding: .utf8)
    }
}

struct ARScanView: UIViewRepresentable {
    @Binding var isScanning: Bool
    @Binding var category: String
    @Binding var statusMsg: String
    @Binding var resultMsg: String?

    func makeUIView(context: Context) -> ARView {
        let v = ARView(frame: .zero)
        v.session.delegate = context.coordinator
        let config = ARWorldTrackingConfiguration()
        config.environmentTexturing = .automatic
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            config.frameSemantics.insert(.sceneDepth)
        }
        v.session.run(config, options: [.resetTracking, .removeExistingAnchors])
        context.coordinator.view = v
        return v
    }

    func updateUIView(_ uiView: ARView, context: Context) {
        context.coordinator.scanning = isScanning
        if isScanning { context.coordinator.startIfNeeded(category: category) } else { context.coordinator.stopIfNeeded() }
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, ARSessionDelegate {
        let parent: ARScanView
        weak var view: ARView?
        var scanning = false
        var startedAt: Date?
        var keyframes = 0
        let maxKeyframes = 18
        let stridePix = 4
        let collector = PointCollector()
        var photo: UIImage?

        init(_ parent: ARScanView) { self.parent = parent }

        func startIfNeeded(category: String) { guard startedAt == nil else { return }; startedAt = Date(); keyframes = 0; collector.pts.removeAll(); parent.statusMsg = "Escaneando… 120–270°" }
        func stopIfNeeded() {
            guard startedAt != nil else { return }
            startedAt = nil; parent.statusMsg = "Procesando y subiendo…"
            Task { await finalizeAndUpload() }
        }

        func session(_ session: ARSession, didUpdate frame: ARFrame) {
            guard scanning, let startedAt else { return }
            if Date().timeIntervalSince(startedAt) > 20 || keyframes >= maxKeyframes { parent.isScanning = false; stopIfNeeded(); return }
            if shouldKeep(frame: frame) {
                keyframes += 1
                appendDepthPoints(frame: frame, stride: stridePix)
                if photo == nil { photo = UIImage(ciImage: CIImage(cvPixelBuffer: frame.capturedImage)) }
                parent.statusMsg = "Frames: \(keyframes)/\(maxKeyframes)  Puntos: \(collector.pts.count)"
            }
        }

        func shouldKeep(frame: ARFrame) -> Bool { if keyframes == 0 { return true }; return (keyframes % 1) == 0 && collector.pts.count/1000 < keyframes*12 }

        func appendDepthPoints(frame: ARFrame, stride: Int) {
            guard let depth = frame.sceneDepth else { return }
            let depthPix = depth.depthMap
            CVPixelBufferLockBaseAddress(depthPix, .readOnly); defer { CVPixelBufferUnlockBaseAddress(depthPix, .readOnly) }
            let w = CVPixelBufferGetWidth(depthPix), h = CVPixelBufferGetHeight(depthPix)
            guard let base = CVPixelBufferGetBaseAddress(depthPix) else { return }
            let fbuf = base.bindMemory(to: Float32.self, capacity: w*h)
            let K = frame.camera.intrinsics
            let fx = K[0][0], fy = K[1][1], cx = K[2][0], cy = K[2][1]
            let T = frame.camera.transform
            for v in stride(from: 0, to: h, by: stride) {
                for u in stride(from: 0, to: w, by: stride) {
                    let z = fbuf[v*w + u]; if !z.isFinite || z <= 0 { continue }
                    let x = (Float(u) - cx)/fx * z; let y = (Float(v) - cy)/fy * z
                    let pCam = simd_float4(x, y, z, 1); let pW = T * pCam
                    collector.add(pW.x, pW.y, pW.z)
                }
            }
        }

        func finalizeAndUpload() async {
            collector.downsample(maxPoints: 150_000)
            let tmp = FileManager.default.temporaryDirectory
            let plyURL = tmp.appendingPathComponent("scan.ply")
            do { try collector.writePLY(to: plyURL) } catch {
                await MainActor.run { self.parent.resultMsg = "Error PLY: \(error.localizedDescription)"; self.parent.statusMsg = "Error" }; return
            }
            let jpgURL = tmp.appendingPathComponent("photo.jpg")
            if let photo, let data = photo.jpegData(compressionQuality: 0.85) { try? data.write(to: jpgURL) }
            let meta: [String:Any] = ["units":"m","scale":1.0,"source":"ios-arkit-depth","frames_kept": keyframes, "angle_covered_deg": 180]
            do {
                let res = try await Uploader.upload(category: parent.category, imageURL: jpgURL, plyURL: plyURL, meta: meta)
                await MainActor.run { self.parent.resultMsg = res; self.parent.statusMsg = "Listo" }
            } catch {
                await MainActor.run { self.parent.resultMsg = "Error upload: \(error.localizedDescription)"; self.parent.statusMsg = "Error" }
            }
        }
    }
}
