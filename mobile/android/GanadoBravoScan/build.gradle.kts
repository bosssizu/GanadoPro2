plugins { id("com.android.application") version "8.4.1"; kotlin("android") version "1.9.24" }
android {
    namespace = "com.ganadobravo.scanner"; compileSdk = 34
    defaultConfig { applicationId = "com.ganadobravo.scanner"; minSdk = 26; targetSdk = 34; versionCode = 1; versionName = "1.0" }
    buildTypes { release { isMinifyEnabled = false } }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("com.google.ar:core:1.45.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
}
