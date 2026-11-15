# 📱 Domos Remote — Aplicación Android Nativa

Cliente móvil nativo para el control, monitorización y réplica en tiempo real del sistema domótico **Domos Smart Home Kiosk**. Desarrollado con **Kotlin**, **Jetpack Compose** y **Material Design 3**.

---

## ✨ Características

* **📺 Réplica en Vivo (Live Screen Mirroring):** Transmisión de pantalla en tiempo real a 60 FPS / baja latencia del terminal Domos con control táctil interactivo (touch forwarding).
* **🌐 Webview Interactiva Directa:** Navegación por la interfaz web local o remota en pantalla completa.
* **⚡ Conexión Híbrida Inteligente:** Conmuta automáticamente entre red local LAN de alta velocidad y túnel seguro Cloudflare según la disponibilidad del WiFi de casa.
* **🚨 Monitor de Incidencias en Tiempo Real:** Detección de anomalías de batería, fallos de red y avisos críticos.
* **🎨 Tema Domos Dark Cyber:** Diseño ergonómico de alto contraste optimizado para pantallas OLED.

---

## 🛠️ Requisitos de Compilación

* **Android Studio** (Koala / Ladybug o superior)
* **JDK:** Versión 17 o superior
* **Android SDK:** Compile SDK 34 (Android 14) / Min SDK 26 (Android 8.0)
* **Gradle:** 8.4+ (incluido mediante `./gradlew`)

---

## ⚙️ Configuración de Endpoints y Datos Propios

Puedes personalizar la dirección de tu servidor Domos de dos formas:

### Opción 1: Directamente en la App (Sin recompilar)
Al iniciar la app, pulsa el icono de engranaje (**Ajustes**) en la barra superior para abrir el diálogo **Configuración de Red Domos**:
* **URL Remota:** Introduce tu túnel Cloudflare (ej. `https://tu-tunel.trycloudflare.com`).
* **URL Local:** Introduce la IP local de tu tablet o servidor Domos (ej. `http://192.168.1.150:8080`).

### Opción 2: En el Código Fuente (Preconfigurado al compilar)
Abre el archivo [`app/src/main/kotlin/com/example/domosremote/data/DomosApiClient.kt`](app/src/main/kotlin/com/example/domosremote/data/DomosApiClient.kt) y define tus URLs por defecto:

```kotlin
object DomosApiClient {
    var baseUrl: String = "https://tu-tunel-cloudflare.trycloudflare.com"
    var localUrl: String = "http://192.168.1.xxx:8080"
    var useRemote: Boolean = true
    ...
}
```

---

## 🚀 Compilar el Proyecto

### Con la Terminal
```bash
# Dar permisos de ejecución al wrapper (si es necesario)
chmod +x gradlew

# Compilar APK en modo Debug
./gradlew assembleDebug

# Compilar APK optimizado para Release
./gradlew assembleRelease
```

El archivo generado se encontrará en:
* **Debug:** `app/build/outputs/apk/debug/app-debug.apk`
* **Release:** `app/build/outputs/apk/release/app-release-unsigned.apk`

### Con Android Studio
1. Abre Android Studio y selecciona **Open**.
2. Navega hasta la carpeta `android` de este repositorio y pulsa **OK**.
3. Espera a que Gradle sincronice las dependencias.
4. Conecta tu teléfono Android por USB (con depuración USB activada) o inicia un emulador.
5. Haz clic en el botón verde **Run** (`Shift + F10`) o selecciona **Build > Build Bundle(s) / APK(s) > Build APK(s)**.

---

## 📂 Estructura del Código

```text
android/
├── app/
│   ├── src/main/
│   │   ├── AndroidManifest.xml
│   │   ├── kotlin/com/example/domosremote/
│   │   │   ├── MainActivity.kt               # Entry point de la aplicación
│   │   │   ├── Navigation.kt                 # Navegación entre vistas
│   │   │   ├── data/
│   │   │   │   ├── DomosApiClient.kt         # Cliente HTTP, telemetría y eventos
│   │   │   │   └── DataRepository.kt         # Repositorio de datos reactivo
│   │   │   └── ui/
│   │   │       ├── main/
│   │   │       │   ├── MainScreen.kt         # UI principal en Jetpack Compose
│   │   │       │   └── MainScreenViewModel.kt# Lógica de estado y refresco
│   │   │       └── theme/                    # Paleta de colores, tipografía y estilo
│   │   └── res/                              # Iconos vectoriales y recursos XML
│   └── build.gradle.kts                      # Dependencias de la app
├── gradle/                                   # Gradle Wrapper
├── build.gradle.kts                          # Configuración raíz del proyecto
└── settings.gradle.kts                       # Módulos y repositorios
```

---

## 📄 Licencia

Este módulo se distribuye bajo licencia **MIT** como parte del proyecto Domos.
