import Foundation
import ARKit
import simd
import CoreVideo

final class DepthCaptureManager: NSObject, ObservableObject, ARSessionDelegate {
    let session = ARSession()
    @Published var keyframes: [Keyframe] = []
    @Published var deviceHasDepth: Bool = false

    private var isRunning = false
    private var lastAddedAngle: Float = 0 // degrees
    private var lastTransform: simd_float4x4? = nil

    func configureSession() {
        let config = ARWorldTrackingConfiguration()
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            config.frameSemantics.insert(.sceneDepth)
            deviceHasDepth = true
        } else {
            deviceHasDepth = false
        }
        config.environmentTexturing = .automatic
        config.sceneReconstruction = deviceHasDepth ? .mesh : []
        session.delegate = self
        session.run(config, options: [.resetTracking, .removeExistingAnchors])
    }

    func start() {
        keyframes.removeAll()
        isRunning = true
        lastTransform = nil
        lastAddedAngle = 0
    }

    func stop() {
        isRunning = false
    }

    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        guard isRunning else { return }
        // Selección por parallax (ángulo entre poses)
        let T = frame.camera.transform
        if let last = lastTransform {
            let yawNow = atan2(T.columns.0.x, T.columns.2.x)
            let yawLast = atan2(last.columns.0.x, last.columns.2.x)
            let deg = abs((yawNow - yawLast) * 180.0 / .pi)
            if deg < 5.0 { return } // espaciar ~5–10°
        }
        lastTransform = T

        // Calidad simple: baja exposición/blur penaliza
        var quality: Float = 1.0
        quality *= Float(max(0.5, min(1.0, frame.camera.exposureDuration.seconds < 1/15 ? 1.0 : 0.7)))
        quality *= frame.camera.trackingState.isLimited ? 0.7 : 1.0

        let depth = frame.sceneDepth?.depthMap // nil si no hay LiDAR
        let kf = Keyframe(
            timestamp: frame.timestamp,
            transform: frame.camera.transform,
            intrinsics: frame.camera.intrinsics,
            imageBuffer: frame.capturedImage,
            depthBuffer: depth,
            cameraResolution: CGSize(width: frame.camera.imageResolution.width, height: frame.camera.imageResolution.height),
            eulerAngles: frame.camera.eulerAngles,
            quality: quality
        )
        keyframes.append(kf)

        // Limitar 20–24 keyframes
        if keyframes.count > 24 {
            keyframes.removeFirst()
        }
    }
}

extension ARCamera.TrackingState {
    var isLimited: Bool {
        switch self {
        case .normal: return false
        default: return true
        }
    }
}
