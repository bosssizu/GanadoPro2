import Foundation

enum Uploader {
    static func uploadPLY(fileURL: URL, meta: UploadMeta, to url: URL, completion: @escaping (Bool, String?) -> Void) {
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        let boundary = "----gb-boundary-\(UUID().uuidString)"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let metaJSON = try? JSONEncoder().encode(meta)
        var body = Data()
        func addField(name: String, value: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }
        func addFile(field: String, filename: String, fileURL: URL, contentType: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(field)\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: \(contentType)\r\n\r\n".data(using: .utf8)!)
            if let d = try? Data(contentsOf: fileURL) {
                body.append(d)
            }
            body.append("\r\n".data(using: .utf8)!)
        }

        addField(name: "sid", value: meta.sid)
        addField(name: "token", value: "ONE_USE_TOKEN_PLACEHOLDER") // reemplaza con real
        addField(name: "category", value: meta.category)
        addField(name: "meta", value: String(data: metaJSON ?? Data(), encoding: .utf8) ?? "{}")
        addFile(field: "file", filename: "model.ply", fileURL: fileURL, contentType: "application/octet-stream")
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        let task = URLSession.shared.uploadTask(with: req, from: body) { data, resp, err in
            if let err = err { completion(false, err.localizedDescription); return }
            guard let http = resp as? HTTPURLResponse else { completion(false, "No HTTP"); return }
            guard (200..<300).contains(http.statusCode) else {
                let msg = data.flatMap{ String(data: $0, encoding: .utf8) } ?? "Status \(http.statusCode)"
                completion(false, msg); return
            }
            completion(true, nil)
        }
        task.resume()
    }
}
