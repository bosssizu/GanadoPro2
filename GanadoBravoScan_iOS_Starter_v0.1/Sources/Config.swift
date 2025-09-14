import Foundation

enum Config {
    // Ajusta a tu backend
    static let uploadURL = URL(string: "https://web-production-4037a.up.railway.app/api/scans/upload")!
    // Universal Link de retorno (opcional)
    static let returnURL = URL(string: "https://web-production-4037a.up.railway.app/scan-done")!
    // Tiempo recomendado de captura
    static let minSeconds: TimeInterval = 12
    static let maxSeconds: TimeInterval = 20
    // Número de keyframes objetivo
    static let minKeyframes = 10
    static let maxKeyframes = 20
}
