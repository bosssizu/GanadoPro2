import Foundation
import simd
import ARKit

struct Keyframe: Identifiable {
    let id = UUID()
    let timestamp: TimeInterval
    let transform: simd_float4x4
    let intrinsics: simd_float3x3
    let imageBuffer: CVPixelBuffer
    let depthBuffer: CVPixelBuffer?
    let cameraResolution: CGSize
    let eulerAngles: simd_float3
    let quality: Float
}

struct UploadMeta: Codable {
    let sid: String
    let category: String
    let durationSec: Double
    let keyframes: Int
    let deviceModel: String
    let hasDepth: Bool
}
