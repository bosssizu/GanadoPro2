import SwiftUI
import ARKit

struct ContentView: View {
    @State private var supported = ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth)
    @State private var isScanning = false
    @State private var category = "levante"
    @State private var statusMsg = "Listo para escanear"
    @State private var resultMsg: String? = nil

    var body: some View {
        VStack(spacing: 12) {
            Picker("Categoría", selection: $category) {
                Text("levante").tag("levante")
                Text("engorde").tag("engorde")
                Text("vaca flaca").tag("vaca flaca")
            }.pickerStyle(.segmented)

            if supported {
                ARScanView(isScanning: $isScanning, category: $category, statusMsg: $statusMsg, resultMsg: $resultMsg)
                    .frame(height: 340)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
            } else {
                VStack(spacing: 12) {
                    Image(systemName: "arkit").font(.system(size: 48))
                    Text("Escaneo 3D no soportado").font(.headline)
                    Text("Usa análisis 2D en la web o fotogrametría externa.")
                        .font(.footnote).foregroundColor(.secondary).multilineTextAlignment(.center)
                }.frame(height: 340)
            }

            Text(statusMsg).font(.footnote).foregroundColor(.secondary)
            HStack {
                Button(supported ? (isScanning ? "Detener" : "Escanear") : "No soportado") {
                    if supported { isScanning.toggle() }
                }.buttonStyle(.borderedProminent).disabled(!supported)

                Button("Abrir análisis 2D (web)") {
                    if let url = URL(string: "https://YOUR-DEPLOY-URL/static/index.html") { UIApplication.shared.open(url) }
                }.buttonStyle(.bordered)
            }

            if let res = resultMsg {
                ScrollView { Text(res).font(.caption).textSelection(.enabled) }
                    .frame(maxHeight: 160)
                    .padding(8)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            Spacer()
        }.padding()
    }
}
