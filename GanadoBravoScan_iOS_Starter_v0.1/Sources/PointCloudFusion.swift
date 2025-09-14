import Foundation
import simd
import Accelerate
import CoreVideo

struct PointXYZRGB {
    var x: Float
    var y: Float
    var z: Float
    var r: UInt8
    var g: UInt8
    var b: UInt8
}

enum PointCloudFusion {
    static func fuse(keyframes: [Keyframe], voxel: Float = 0.01, minNeighbors: Int = 8, radius: Float = 0.05) -> [PointXYZRGB] {
        guard !keyframes.isEmpty else { return [] }
        var pts: [PointXYZRGB] = []
        for kf in keyframes {
            guard let depth = kf.depthBuffer else { continue }
            pts.append(contentsOf: unproject(depth: depth, color: kf.imageBuffer, intrinsics: kf.intrinsics, pose: kf.transform))
        }
        // Downsample por voxel y outlier removal básicos
        let ds = voxelDownsample(pts, voxel: voxel)
        let clean = radiusOutlierRemoval(ds, k: minNeighbors, r: radius)
        return clean
    }

    static func unproject(depth: CVPixelBuffer, color: CVPixelBuffer, intrinsics: simd_float3x3, pose: simd_float4x4) -> [PointXYZRGB] {
        CVPixelBufferLockBaseAddress(depth, .readOnly)
        CVPixelBufferLockBaseAddress(color, .readOnly)
        defer {
            CVPixelBufferUnlockBaseAddress(depth, .readOnly)
            CVPixelBufferUnlockBaseAddress(color, .readOnly)
        }
        let w = CVPixelBufferGetWidth(depth)
        let h = CVPixelBufferGetHeight(depth)
        let rowBytes = CVPixelBufferGetBytesPerRow(depth)
        guard let dbase = CVPixelBufferGetBaseAddress(depth)?.assumingMemoryBound(to: Float32.self) else { return [] }

        let cw = CVPixelBufferGetWidth(color)
        let ch = CVPixelBufferGetHeight(color)
        let cfmt = CVPixelBufferGetPixelFormatType(color)
        // Captured image es YUV (Bi-Planar). Convertimos a gris simple para colorear neutral.
        // Para simplicidad: color neutro gris; puedes mapear Y plane si quieres más realismo.
        var out: [PointXYZRGB] = []
        let fx = intrinsics[0,0], fy = intrinsics[1,1], cx = intrinsics[2,0], cy = intrinsics[2,1]
        let step = max(1, w / 320) // subsample rápido
        for v in stride(from: 0, to: h, by: step) {
            for u in stride(from: 0, to: w, by: step) {
                let idx = v * (rowBytes/MemoryLayout<Float32>.size) + u
                let z = dbase[idx]
                if !z.isFinite || z <= 0.1 || z > 8.0 { continue }
                let x = (Float(u) - cx) * z / fx
                let y = (Float(v) - cy) * z / fy
                let pCam = simd_float4(x, y, z, 1.0)
                let pWorld = pose * pCam
                let r: UInt8 = 200, g: UInt8 = 200, b: UInt8 = 200
                out.append(PointXYZRGB(x: pWorld.x, y: pWorld.y, z: pWorld.z, r: r, g: g, b: b))
            }
        }
        return out
    }

    static func voxelDownsample(_ pts: [PointXYZRGB], voxel: Float) -> [PointXYZRGB] {
        guard voxel > 0 else { return pts }
        var grid: [Int64: PointXYZRGB] = [:]
        let inv = 1.0 / Double(voxel)
        for p in pts {
            let ix = Int64((Double(p.x)*inv).rounded())
            let iy = Int64((Double(p.y)*inv).rounded())
            let iz = Int64((Double(p.z)*inv).rounded())
            let key = (ix << 42) ^ (iy << 21) ^ iz
            grid[key] = p
        }
        return Array(grid.values)
    }

    static func radiusOutlierRemoval(_ pts: [PointXYZRGB], k: Int, r: Float) -> [PointXYZRGB] {
        guard k > 0 else { return pts }
        var out: [PointXYZRGB] = []
        let r2 = r*r
        for i in 0..<pts.count {
            let pi = pts[i]
            var cnt = 0
            // naive O(n^2) — suficiente para 80–150k puntos si voxel > 1 cm; optimízalo con grid si hace falta.
            for j in 0..<pts.count where j != i {
                let pj = pts[j]
                let dx = pi.x - pj.x, dy = pi.y - pj.y, dz = pi.z - pj.z
                if dx*dx + dy*dy + dz*dz <= r2 {
                    cnt += 1
                    if cnt >= k { break }
                }
            }
            if cnt >= k { out.append(pi) }
        }
        return out
    }
}
