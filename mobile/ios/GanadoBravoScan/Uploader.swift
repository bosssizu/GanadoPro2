import Foundation

struct Uploader {
    static func upload(category: String, imageURL: URL, plyURL: URL, meta: [String:Any]) async throws -> String {
        var req = URLRequest(url: Config.backendURL)
        req.httpMethod = "POST"
        let boundary = "----GB\(UUID().uuidString)"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        func addField(_ name: String, _ value: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }
        func addFile(_ name: String, _ filename: String, _ mime: String, _ url: URL) throws {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: \(mime)\r\n\r\n".data(using: .utf8)!)
            body.append(try Data(contentsOf: url))
            body.append("\r\n".data(using: .utf8)!)
        }

        addField("category", category)
        addField("pro", "1")
        if let json = try? JSONSerialization.data(withJSONObject: meta, options: []),
           let s = String(data: json, encoding: .utf8) { addField("meta_json", s) }
        try? addFile("file", "photo.jpg", "image/jpeg", imageURL)
        try addFile("mesh_file", "scan.ply", "application/octet-stream", plyURL)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        let (data, resp) = try await URLSession.shared.upload(for: req, from: body)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? -1
        return "Status: \(code)\n\n" + (String(data: data, encoding: .utf8) ?? "")
    }
}
