import SwiftUI

@main
struct PhotogramApp: App {
    @StateObject private var store = ScanStore()

    var body: some Scene {
        WindowGroup {
            ScansListView()
                .environmentObject(store)
        }
    }
}
