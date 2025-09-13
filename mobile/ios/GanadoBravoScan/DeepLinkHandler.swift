import Foundation
import SwiftUI

class DeepLinkHandler: ObservableObject {
    static let shared = DeepLinkHandler()
    func handle(url: URL) {
        // ganadobravo://scan?category=...&return=...
        guard url.scheme == "ganadobravo" else { return }
        if url.host == "scan" {
            NotificationCenter.default.post(name: .startScan, object: url)
        }
    }
}

extension Notification.Name {
    static let startScan = Notification.Name("startScan")
}
