import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @State private var category: String = "levante"
    @State private var status: String = "Listo"
    @State private var returnURL: URL? = nil

    var body: some View {
        NavigationView {
            VStack(spacing: 16) {
                Text("GanadoBravo Scan (demo)")
                    .font(.headline)
                Text("Este starter abre un flujo de escaneo 3D (ARKit SceneDepth).")
                    .font(.subheadline)
                Text(status).font(.caption).foregroundColor(.secondary)
                Button("Simular escaneo y enviar") {
                    status = "Simulando PLY/OBJ y subiendo..."
                    // Aquí deberías exportar el PLY/OBJ y hacer POST a Config.backendURL
                }
                .buttonStyle(.borderedProminent)
                Spacer()
            }
            .padding()
            .onReceive(NotificationCenter.default.publisher(for: .startScan)) { note in
                if let url = note.object as? URL,
                   let comps = URLComponents(url: url, resolvingAgainstBaseURL: false) {
                    let q = comps.queryItems ?? []
                    if let c = q.first(where: { $0.name == "category" })?.value {
                        category = c
                    }
                    if let r = q.first(where: { $0.name == "return" })?.value,
                       let u = URL(string: r) {
                        returnURL = u
                    }
                    status = "Deep link recibido. Iniciando escaneo… (demo)"
                }
            }
            .navigationTitle("Escáner 3D")
        }
    }
}
