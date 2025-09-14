import Foundation

enum PLYWriter {
    static func writeASCII(points: [PointXYZRGB], to url: URL) throws {
        var header = ""
        header += "ply\n"
        header += "format ascii 1.0\n"
        header += "element vertex \(points.count)\n"
        header += "property float x\n"
        header += "property float y\n"
        header += "property float z\n"
        header += "property uchar red\n"
        header += "property uchar green\n"
        header += "property uchar blue\n"
        header += "end_header\n"
        var body = String()
        body.reserveCapacity(points.count * 24)
        for p in points {
            body += String(format: "%.5f %.5f %.5f %d %d %d\n", p.x, p.y, p.z, p.r, p.g, p.b)
        }
        let data = (header + body).data(using: .utf8)!
        try data.write(to: url, options: .atomic)
    }
}
