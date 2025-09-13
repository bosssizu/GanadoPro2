import SwiftUI

@main
struct GanadoBravoScanApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onOpenURL { url in
                    DeepLinkHandler.shared.handle(url: url)
                }
        }
    }
}
