package com.example.domosremote.ui.main

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.domosremote.data.CalendarEvent
import com.example.domosremote.data.DomosApiClient
import com.example.domosremote.data.HomeIncident
import com.example.domosremote.ui.theme.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.InputStream
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.unit.IntOffset
import com.example.domosremote.R
import java.net.HttpURLConnection
import java.net.URL

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: MainScreenViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    var showUrlDialog by remember { mutableStateOf(false) }
    var isFullscreenMirror by remember { mutableStateOf(false) }

    val unresolvedCount = uiState.incidents.count { !it.resolved }
    val colorScheme = MaterialTheme.colorScheme

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = colorScheme.background,
        topBar = {
            if (!isFullscreenMirror) {
                TopAppBar(
                title = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        Image(
                            painter = painterResource(id = R.drawable.domos_logo),
                            contentDescription = "Logo Domos",
                            modifier = Modifier
                                .size(32.dp)
                                .clip(RoundedCornerShape(8.dp))
                        )
                        Text(
                            "DOMOS",
                            fontWeight = FontWeight.Black,
                            letterSpacing = 2.sp,
                            color = colorScheme.primary,
                            fontSize = 20.sp
                        )
                    }
                },
                actions = {
                    // Status Badge (Cloudflare / Local)
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = if (uiState.status.isOnline) colorScheme.secondary.copy(alpha = 0.15f) else colorScheme.error.copy(alpha = 0.15f),
                        border = androidx.compose.foundation.BorderStroke(
                            1.dp,
                            if (uiState.status.isOnline) colorScheme.secondary else colorScheme.error
                        ),
                        modifier = Modifier
                            .padding(end = 4.dp)
                            .clickable { showUrlDialog = true }
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(CircleShape)
                                    .background(if (uiState.status.isOnline) colorScheme.secondary else colorScheme.error)
                            )
                            Text(
                                if (uiState.useRemote) "Auto · Remoto" else "Auto · WiFi",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = if (uiState.status.isOnline) colorScheme.secondary else colorScheme.error
                            )
                        }
                    }

                    // Theme Toggle: Light / Dark
                    IconButton(onClick = { viewModel.toggleTheme() }) {
                        Icon(
                            imageVector = if (uiState.isDarkTheme) Icons.Outlined.LightMode else Icons.Outlined.DarkMode,
                            contentDescription = "Cambiar tema",
                            tint = colorScheme.primary
                        )
                    }

                    // Refresh
                    IconButton(onClick = { viewModel.autoDetectAndRefresh() }) {
                        Icon(Icons.Outlined.Refresh, contentDescription = "Refrescar", tint = Color(0xFF38BDF8))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = colorScheme.surface,
                    titleContentColor = colorScheme.onSurface
                )
            )
            }
        },
        bottomBar = {
            if (!isFullscreenMirror) {
            NavigationBar(
                containerColor = colorScheme.surface,
                contentColor = colorScheme.onSurface
            ) {
                NavigationBarItem(
                    selected = uiState.activeTab == 0,
                    onClick = { viewModel.setTab(0) },
                    icon = { Icon(Icons.Outlined.TabletAndroid, contentDescription = "Táctil") },
                    label = { Text("Táctil Kiosko") },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = colorScheme.onPrimary,
                        selectedTextColor = colorScheme.primary,
                        indicatorColor = colorScheme.primary,
                        unselectedIconColor = colorScheme.onSurfaceVariant,
                        unselectedTextColor = colorScheme.onSurfaceVariant
                    )
                )
                NavigationBarItem(
                    selected = uiState.activeTab == 1,
                    onClick = { viewModel.setTab(1) },
                    icon = { Icon(Icons.Outlined.RadioButtonChecked, contentDescription = "Mensajes") },
                    label = { Text("Mensajes") },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = colorScheme.onPrimary,
                        selectedTextColor = colorScheme.primary,
                        indicatorColor = colorScheme.primary,
                        unselectedIconColor = colorScheme.onSurfaceVariant,
                        unselectedTextColor = colorScheme.onSurfaceVariant
                    )
                )
                NavigationBarItem(
                    selected = uiState.activeTab == 2,
                    onClick = { viewModel.setTab(2) },
                    icon = {
                        BadgedBox(
                            badge = {
                                if (unresolvedCount > 0) {
                                    Badge(containerColor = colorScheme.error) {
                                        Text("$unresolvedCount")
                                    }
                                }
                            }
                        ) {
                            Icon(Icons.Outlined.Shield, contentDescription = "Incidencias")
                        }
                    },
                    label = { Text("Incidencias") },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = colorScheme.onPrimary,
                        selectedTextColor = colorScheme.primary,
                        indicatorColor = colorScheme.primary,
                        unselectedIconColor = colorScheme.onSurfaceVariant,
                        unselectedTextColor = colorScheme.onSurfaceVariant
                    )
                )
                NavigationBarItem(
                    selected = uiState.activeTab == 3,
                    onClick = { viewModel.setTab(3) },
                    icon = { Icon(Icons.Outlined.Tune, contentDescription = "Ajustes") },
                    label = { Text("Ajustes") },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = colorScheme.onPrimary,
                        selectedTextColor = colorScheme.primary,
                        indicatorColor = colorScheme.primary,
                        unselectedIconColor = colorScheme.onSurfaceVariant,
                        unselectedTextColor = colorScheme.onSurfaceVariant
                    )
                )
            }
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (uiState.activeTab) {
                0 -> DualKioskScreen(activeUrl = DomosApiClient.getActiveUrl(), isFullscreen = isFullscreenMirror, onToggleFullscreen = { isFullscreenMirror = it })
                1 -> FamilyMessagesScreen(
                    isSending = uiState.isSendingMessage,
                    feedback = uiState.messageFeedback,
                    isSuccess = uiState.isSuccessMessage,
                    onSend = { sender, text, speak ->
                        viewModel.sendFamilyMessage(sender, text, speak)
                    }
                )
                2 -> IncidentsAndCalendarScreen(
                    incidents = uiState.incidents,
                    calendar = uiState.calendarEvents,
                    onResolve = { viewModel.resolveIncident(it) },
                    onRefresh = { viewModel.autoDetectAndRefresh() }
                )
                3 -> ControlsScreen(
                    uiState = uiState,
                    onToggleTheme = { viewModel.toggleTheme() },
                    onSetBrightness = { viewModel.setBrightness(it) },
                    onTriggerDoorbell = { viewModel.triggerDoorbell() },
                    onToggleMode = { viewModel.toggleConnectionMode(it) },
                    onOpenConfig = { showUrlDialog = true }
                )
            }
        }
    }

    if (showUrlDialog) {
        UrlConfigDialog(
            remoteUrl = uiState.remoteUrl,
            localUrl = uiState.localUrl,
            useRemote = uiState.useRemote,
            onDismiss = { showUrlDialog = false },
            onSave = { remote, local, useRem ->
                viewModel.updateUrls(remote, local)
                viewModel.toggleConnectionMode(useRem)
                showUrlDialog = false
            }
        )
    }
}

// ========================================================
// REDISTRIBUTED MOBILE TOUCH SCREEN (TÁCTIL WEB & ESPEJO)
// ========================================================
@Composable
fun DualKioskScreen(
    activeUrl: String,
    isFullscreen: Boolean = false,
    onToggleFullscreen: (Boolean) -> Unit = {}
) {
    var viewMode by remember { mutableStateOf(0) } // Default: 0 (Espejo Físico con Control Táctil Directo)
    val colorScheme = MaterialTheme.colorScheme

    Column(modifier = Modifier.fillMaxSize()) {
        if (!isFullscreen) {
            // Mode Selector Bar (Chips designed to fit neatly on narrow screens)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(colorScheme.surface)
                    .padding(horizontal = 12.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                FilterChip(
                    selected = viewMode == 0,
                    onClick = { viewMode = 0 },
                    label = { Text("🎮 Espejo Táctil 16:9", fontSize = 12.sp, fontWeight = FontWeight.SemiBold) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = colorScheme.primary,
                        selectedLabelColor = colorScheme.onPrimary,
                        containerColor = colorScheme.surfaceVariant,
                        labelColor = colorScheme.onSurface
                    ),
                    modifier = Modifier.weight(1f)
                )

                FilterChip(
                    selected = viewMode == 1,
                    onClick = { viewMode = 1 },
                    label = { Text("🌐 Web Móvil Directa", fontSize = 12.sp) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = colorScheme.primary,
                        selectedLabelColor = colorScheme.onPrimary,
                        containerColor = colorScheme.surfaceVariant,
                        labelColor = colorScheme.onSurface
                    ),
                    modifier = Modifier.weight(1f)
                )
            }
        }

        Box(modifier = Modifier.weight(1f)) {
            if (viewMode == 1 && !isFullscreen) {
                KioskWebInteractiveScreen(activeUrl = activeUrl)
            } else {
                LiveScreenMirrorView(
                    baseUrl = activeUrl,
                    isFullscreen = isFullscreen,
                    onToggleFullscreen = onToggleFullscreen
                )
            }
        }
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun KioskWebInteractiveScreen(activeUrl: String) {
    var isLoading by remember { mutableStateOf(true) }
    var webViewInstance by remember { mutableStateOf<WebView?>(null) }
    val context = LocalContext.current
    val colorScheme = MaterialTheme.colorScheme
    val scope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize()) {
        // Mobile Action Strip: Reload, Zoom & External
        Surface(
            color = colorScheme.surfaceVariant,
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(7.dp)
                            .clip(CircleShape)
                            .background(colorScheme.secondary)
                    )
                    Text("Liquid UI Kiosk", fontSize = 11.sp, fontWeight = FontWeight.SemiBold, color = colorScheme.onSurface)
                }

                Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    IconButton(
                        onClick = { webViewInstance?.reload() },
                        modifier = Modifier.size(32.dp)
                    ) {
                        Icon(Icons.Outlined.Refresh, contentDescription = "Recargar", tint = Color(0xFF38BDF8), modifier = Modifier.size(18.dp))
                    }

                    IconButton(
                        onClick = {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(activeUrl))
                            context.startActivity(intent)
                        },
                        modifier = Modifier.size(32.dp)
                    ) {
                        Icon(Icons.Outlined.OpenInBrowser, contentDescription = "Navegador", tint = colorScheme.primary, modifier = Modifier.size(18.dp))
                    }
                }
            }
        }

        // Web Content Viewport
        Box(modifier = Modifier.weight(1f)) {
            AndroidView(
                factory = { ctx ->
                    WebView(ctx).apply {
                        settings.javaScriptEnabled = true
                        settings.domStorageEnabled = true
                        settings.useWideViewPort = false
                        settings.loadWithOverviewMode = false
                        settings.setSupportZoom(true)
                        settings.builtInZoomControls = true
                        settings.displayZoomControls = false
                        settings.cacheMode = WebSettings.LOAD_DEFAULT

                        webViewClient = object : WebViewClient() {
                            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                                isLoading = true
                            }
                            override fun onPageFinished(view: WebView?, url: String?) {
                                isLoading = false
                            }
                        }
                        webChromeClient = WebChromeClient()
                        loadUrl(activeUrl)
                        webViewInstance = this
                    }
                },
                update = { view ->
                    if (view.url != activeUrl) {
                        view.loadUrl(activeUrl)
                    }
                },
                modifier = Modifier.fillMaxSize()
            )

            if (isLoading) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(colorScheme.background.copy(alpha = 0.7f)),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = colorScheme.primary)
                }
            }
        }

        // Mobile Quick-Actions Dock (One-touch shortcuts for mobile comfort)
        Surface(
            color = colorScheme.surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline.copy(alpha = 0.5f)),
            modifier = Modifier.fillMaxWidth()
        ) {
            LazyRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 8.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                item {
                    Button(
                        onClick = {
                            scope.launch {
                                DomosApiClient.sendTap(0.90f, 0.92f) // Tap Panel
                            }
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = colorScheme.primary, contentColor = colorScheme.onPrimary),
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                    ) {
                        Text("🎛️ Panel", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                }

                item {
                    OutlinedButton(
                        onClick = {
                            scope.launch {
                                DomosApiClient.sendTap(0.72f, 0.92f) // Tap Cámaras
                            }
                        },
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                    ) {
                        Text("📹 Cámaras", fontSize = 11.sp)
                    }
                }

                item {
                    OutlinedButton(
                        onClick = {
                            scope.launch {
                                DomosApiClient.sendTap(0.61f, 0.92f) // Tap Luz Cocina 1
                            }
                        },
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                    ) {
                        Text("💡 Cocina 1", fontSize = 11.sp)
                    }
                }

                item {
                    OutlinedButton(
                        onClick = {
                            scope.launch {
                                DomosApiClient.sendTap(0.55f, 0.92f) // Tap Asistente Domos
                            }
                        },
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                    ) {
                        Text("🎙️ Domos", fontSize = 11.sp)
                    }
                }

                item {
                    OutlinedButton(
                        onClick = {
                            scope.launch {
                                DomosApiClient.sendTap(0.50f, 0.92f) // Tap Tema Kiosko
                            }
                        },
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                    ) {
                        Text("☀️/🌙 Kiosko", fontSize = 11.sp)
                    }
                }
            }
        }
    }
}

@Composable
fun LiveScreenMirrorView(
    baseUrl: String,
    isFullscreen: Boolean = false,
    onToggleFullscreen: (Boolean) -> Unit = {}
) {
    var screenBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var lastUpdated by remember { mutableStateOf("") }
    var autoRefresh by remember { mutableStateOf(true) }
    var containerSize by remember { mutableStateOf(IntSize.Zero) }
    var touchFeedback by remember { mutableStateOf<Offset?>(null) }
    val colorScheme = MaterialTheme.colorScheme
    val scope = rememberCoroutineScope()

    suspend fun fetchScreen(): Bitmap? = withContext(Dispatchers.IO) {
        try {
            val url = URL("$baseUrl/api/screen/live.png?t=${System.currentTimeMillis()}")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 3000
                readTimeout = 3000
                requestMethod = "GET"
            }
            if (conn.responseCode == 200) {
                val input: InputStream = conn.inputStream
                val bmp = BitmapFactory.decodeStream(input)
                input.close()
                bmp
            } else {
                null
            }
        } catch (e: Exception) {
            null
        }
    }

    LaunchedEffect(baseUrl, autoRefresh) {
        while (autoRefresh) {
            val bmp = fetchScreen()
            if (bmp != null) {
                screenBitmap = bmp
                lastUpdated = java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault()).format(java.util.Date())
            }
            delay(1500)
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
        contentAlignment = Alignment.Center
    ) {
        val bmp = screenBitmap
        if (bmp != null) {
            Column(
                modifier = Modifier.fillMaxSize(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                if (!isFullscreen) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(colorScheme.surface)
                            .padding(horizontal = 14.dp, vertical = 6.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(CircleShape)
                                    .background(colorScheme.error)
                            )
                            Text("ESPEJO 16:9", color = colorScheme.error, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            Text("· $lastUpdated", color = colorScheme.onSurfaceVariant, fontSize = 11.sp)
                        }

                        OutlinedButton(
                            onClick = { onToggleFullscreen(true) },
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                            modifier = Modifier.height(28.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.primary)
                        ) {
                            Icon(Icons.Outlined.Fullscreen, contentDescription = null, tint = colorScheme.primary, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Pantalla Completa", fontSize = 11.sp, color = colorScheme.primary, fontWeight = FontWeight.SemiBold)
                        }
                    }
                }

                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                        .padding(if (isFullscreen) 0.dp else 6.dp)
                        .then(
                            if (!isFullscreen) Modifier.border(1.dp, colorScheme.outline, RoundedCornerShape(12.dp)).clip(RoundedCornerShape(12.dp))
                            else Modifier
                        )
                        .background(Color.Black)
                        .onSizeChanged { containerSize = it }
                        .pointerInput(Unit) {
                            detectTapGestures { offset ->
                                if (containerSize.width > 0 && containerSize.height > 0) {
                                    touchFeedback = offset
                                    scope.launch {
                                        delay(450)
                                        touchFeedback = null
                                    }

                                    val cw = containerSize.width.toFloat()
                                    val ch = containerSize.height.toFloat()
                                    val targetRatio = 1366f / 768f
                                    val containerRatio = cw / ch

                                    val (dispW, dispH, offX, offY) = if (containerRatio < targetRatio) {
                                        val h = cw / targetRatio
                                        listOf(cw, h, 0f, (ch - h) / 2f)
                                    } else {
                                        val w = ch * targetRatio
                                        listOf(w, ch, (cw - w) / 2f, 0f)
                                    }

                                    val localX = offset.x - offX
                                    val localY = offset.y - offY

                                    if (localX in 0f..dispW && localY in 0f..dispH) {
                                        val xPct = (localX / dispW).coerceIn(0f, 1f)
                                        val yPct = (localY / dispH).coerceIn(0f, 1f)
                                        scope.launch {
                                            DomosApiClient.sendTap(xPct, yPct)
                                            delay(250)
                                            val refreshed = fetchScreen()
                                            if (refreshed != null) screenBitmap = refreshed
                                            delay(350)
                                            val refreshed2 = fetchScreen()
                                            if (refreshed2 != null) screenBitmap = refreshed2
                                        }
                                    }
                                }
                            }
                        },
                    contentAlignment = Alignment.Center
                ) {
                    Image(
                        bitmap = bmp.asImageBitmap(),
                        contentDescription = "Espejo Pantalla Domos",
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Fit
                    )

                    // Touch ripple feedback
                    touchFeedback?.let { tf ->
                        Box(
                            modifier = Modifier
                                .offset { IntOffset(tf.x.toInt() - 20, tf.y.toInt() - 20) }
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(colorScheme.primary.copy(alpha = 0.40f))
                                .border(2.dp, colorScheme.primary, CircleShape)
                        )
                    }

                    // Floating Exit Fullscreen Button
                    if (isFullscreen) {
                        IconButton(
                            onClick = { onToggleFullscreen(false) },
                            modifier = Modifier
                                .align(Alignment.TopEnd)
                                .padding(16.dp)
                                .size(42.dp)
                                .background(Color.Black.copy(alpha = 0.7f), CircleShape)
                                .border(1.dp, Color.White.copy(alpha = 0.5f), CircleShape)
                        ) {
                            Icon(
                                Icons.Outlined.FullscreenExit,
                                contentDescription = "Salir de pantalla completa",
                                tint = Color.White,
                                modifier = Modifier.size(24.dp)
                            )
                        }
                    }
                }
            }
        } else {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                CircularProgressIndicator(color = colorScheme.primary)
                Text("Conectando con la pantalla del Kiosko...", color = Color.White, fontSize = 13.sp)
            }
        }
    }
}

// ========================================================
// MENSAJES DE FAMILIA SCREEN
// ========================================================
@Composable
fun FamilyMessagesScreen(
    isSending: Boolean,
    feedback: String?,
    isSuccess: Boolean,
    onSend: (String, String, Boolean) -> Unit
) {
    var selectedSender by remember { mutableStateOf("Papá 🚗") }
    var customSender by remember { mutableStateOf("") }
    var isCustomSender by remember { mutableStateOf(false) }
    var messageText by remember { mutableStateOf("") }
    var speakAloud by remember { mutableStateOf(true) }

    val senders = listOf("Papá 🚗", "Mamá 👩", "Hijos 👦👧", "Otro ✏️")
    val presets = listOf(
        "🚗 Voy de camino a casa.",
        "⏰ Llego en 10 minutos.",
        "🍽️ ¿Podéis ir poniendo la mesa?",
        "🛒 ¿Hace falta comprar pan o leche?",
        "❤️ ¡Hola familia! Os mando un abrazo.",
        "⚠️ No abráis la puerta a nadie."
    )
    val colorScheme = MaterialTheme.colorScheme

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("¿Quién envía el mensaje?", fontWeight = FontWeight.Bold, color = colorScheme.onSurface)

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    senders.forEach { s ->
                        val isSelected = (!isCustomSender && selectedSender == s) || (isCustomSender && s.contains("Otro"))
                        FilterChip(
                            selected = isSelected,
                            onClick = {
                                if (s.contains("Otro")) {
                                    isCustomSender = true
                                } else {
                                    isCustomSender = false
                                    selectedSender = s
                                }
                            },
                            label = { Text(s, fontSize = 11.sp) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = colorScheme.primary,
                                selectedLabelColor = colorScheme.onPrimary,
                                containerColor = colorScheme.surfaceVariant,
                                labelColor = colorScheme.onSurface
                            ),
                            modifier = Modifier.weight(1f)
                        )
                    }
                }

                if (isCustomSender) {
                    OutlinedTextField(
                        value = customSender,
                        onValueChange = { customSender = it },
                        label = { Text("Nombre del remitente") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = colorScheme.primary,
                            unfocusedBorderColor = colorScheme.outline
                        )
                    )
                }
            }
        }

        // Card Escribir Mensaje
        Card(
            colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Escribe el mensaje para la pantalla", fontWeight = FontWeight.Bold, color = colorScheme.onSurface)

                OutlinedTextField(
                    value = messageText,
                    onValueChange = { messageText = it },
                    placeholder = { Text("Escribe un mensaje para que se vea en el marco...") },
                    modifier = Modifier.fillMaxWidth().height(120.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = colorScheme.primary,
                        unfocusedBorderColor = colorScheme.outline
                    )
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Leer en voz alta por el altavoz", color = colorScheme.onSurface, fontSize = 13.sp)
                    Switch(
                        checked = speakAloud,
                        onCheckedChange = { speakAloud = it },
                        colors = SwitchDefaults.colors(checkedThumbColor = colorScheme.primary)
                    )
                }

                Button(
                    onClick = {
                        val sender = if (isCustomSender) customSender.ifBlank { "Familia" } else selectedSender
                        onSend(sender, messageText, speakAloud)
                        messageText = ""
                    },
                    modifier = Modifier.fillMaxWidth().height(48.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = colorScheme.primary, contentColor = colorScheme.onPrimary),
                    enabled = !isSending && messageText.isNotBlank()
                ) {
                    if (isSending) {
                        CircularProgressIndicator(color = colorScheme.onPrimary, modifier = Modifier.size(20.dp))
                    } else {
                        Icon(Icons.Outlined.RadioButtonChecked, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Emitir Mensaje en Domos", fontWeight = FontWeight.Bold)
                    }
                }

                if (feedback != null) {
                    Text(
                        feedback,
                        color = if (isSuccess) colorScheme.secondary else colorScheme.error,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }

        // Mensajes Rápidos
        Card(
            colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Plantillas rápidas", fontWeight = FontWeight.Bold, color = colorScheme.onSurface)
                presets.forEach { p ->
                    Surface(
                        shape = RoundedCornerShape(10.dp),
                        color = colorScheme.surfaceVariant,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { messageText = p }
                    ) {
                        Text(p, modifier = Modifier.padding(12.dp), fontSize = 13.sp, color = colorScheme.onSurface)
                    }
                }
            }
        }
    }
}

// ========================================================
// INCIDENCIAS Y CALENDARIO SCREEN
// ========================================================
@Composable
fun IncidentsAndCalendarScreen(
    incidents: List<HomeIncident>,
    calendar: List<CalendarEvent>,
    onResolve: (String) -> Unit,
    onRefresh: () -> Unit
) {
    val colorScheme = MaterialTheme.colorScheme

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Text("Registro de Incidencias Domóticas", fontWeight = FontWeight.Black, fontSize = 18.sp, color = colorScheme.onBackground)
        }

        if (incidents.isEmpty()) {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
                    shape = RoundedCornerShape(16.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(24.dp).fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text("🛡️", fontSize = 32.sp)
                        Text("Todo en orden", fontWeight = FontWeight.Bold, color = colorScheme.onSurface)
                        Text("No hay incidencias registradas en el sistema.", color = colorScheme.onSurfaceVariant, fontSize = 13.sp)
                    }
                }
            }
        } else {
            items(incidents) { inc ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
                    shape = RoundedCornerShape(16.dp),
                    border = androidx.compose.foundation.BorderStroke(
                        1.dp,
                        if (inc.resolved) colorScheme.outline else colorScheme.error.copy(alpha = 0.5f)
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(inc.title, fontWeight = FontWeight.Bold, color = colorScheme.onSurface)
                            Surface(
                                shape = RoundedCornerShape(6.dp),
                                color = if (inc.resolved) colorScheme.secondary.copy(alpha = 0.2f) else colorScheme.error.copy(alpha = 0.2f)
                            ) {
                                Text(
                                    if (inc.resolved) "Resuelta" else "Pendiente",
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                    fontSize = 11.sp,
                                    color = if (inc.resolved) colorScheme.secondary else colorScheme.error
                                )
                            }
                        }
                        if (inc.description.isNotBlank()) {
                            Text(inc.description, fontSize = 13.sp, color = colorScheme.onSurfaceVariant)
                        }
                        Text("${inc.source} · ${inc.timestamp}", fontSize = 11.sp, color = colorScheme.onSurfaceVariant)

                        if (!inc.resolved) {
                            Button(
                                onClick = { onResolve(inc.id) },
                                modifier = Modifier.fillMaxWidth().height(36.dp),
                                shape = RoundedCornerShape(8.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = colorScheme.primary, contentColor = colorScheme.onPrimary)
                            ) {
                                Text("Marcar como Resuelta", fontSize = 12.sp)
                            }
                        }
                    }
                }
            }
        }
    }
}

// ========================================================
// AJUSTES & CONTROL SCREEN
// ========================================================
@Composable
fun ControlsScreen(
    uiState: DomosUiState,
    onToggleTheme: () -> Unit,
    onSetBrightness: (Int) -> Unit,
    onTriggerDoorbell: () -> Unit,
    onToggleMode: (Boolean) -> Unit,
    onOpenConfig: () -> Unit
) {
    val colorScheme = MaterialTheme.colorScheme

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // TEMA DE LA APLICACIÓN (CLARO / OSCURO)
        Card(
            colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Tema Visual de la Aplicación", fontWeight = FontWeight.Bold, color = colorScheme.onSurface)

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = { if (uiState.isDarkTheme) onToggleTheme() },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (!uiState.isDarkTheme) colorScheme.primary else colorScheme.surfaceVariant,
                            contentColor = if (!uiState.isDarkTheme) colorScheme.onPrimary else colorScheme.onSurface
                        )
                    ) {
                        Text("☀️ Modo Claro", fontWeight = FontWeight.SemiBold)
                    }

                    Button(
                        onClick = { if (!uiState.isDarkTheme) onToggleTheme() },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (uiState.isDarkTheme) colorScheme.primary else colorScheme.surfaceVariant,
                            contentColor = if (uiState.isDarkTheme) colorScheme.onPrimary else colorScheme.onSurface
                        )
                    ) {
                        Text("🌙 Modo Oscuro", fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }

        // Estado del Kiosko ASUS
        Card(
            colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Estado del Kiosko ASUS T200TA", color = colorScheme.onSurfaceVariant, fontSize = 12.sp)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text("${uiState.status.batteryPct}%", fontSize = 32.sp, fontWeight = FontWeight.Black, color = colorScheme.primary)
                        Text(
                            if (uiState.status.batteryStatus == "Charging" || uiState.status.batteryStatus == "Full") "⚡ Cargando" else "🔋 Batería",
                            color = colorScheme.onSurfaceVariant,
                            fontSize = 14.sp
                        )
                    }

                    Surface(shape = RoundedCornerShape(8.dp), color = colorScheme.surfaceVariant) {
                        Text("Guard: 30% - 70%", modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), fontSize = 11.sp, color = colorScheme.secondary)
                    }
                }
            }
        }

        // Control de Brillo
        Card(
            colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Brillo de Pantalla Kiosko", fontWeight = FontWeight.Bold, color = colorScheme.onSurface)
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    val levels = listOf(10 to "Noche 🌙", 40 to "Eco 🍃", 75 to "Normal 🖥️", 100 to "Máx ☀️")
                    levels.forEach { (pct, label) ->
                        Button(
                            onClick = { onSetBrightness(pct) },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(10.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = colorScheme.surfaceVariant, contentColor = colorScheme.onSurface),
                            contentPadding = PaddingValues(4.dp)
                        ) {
                            Text(label, fontSize = 11.sp)
                        }
                    }
                }
            }
        }

        // Timbre Tuya
        Card(
            colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Acciones Rápidas", fontWeight = FontWeight.Bold, color = colorScheme.onSurface)

                Button(
                    onClick = onTriggerDoorbell,
                    modifier = Modifier.fillMaxWidth().height(48.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = colorScheme.secondary.copy(alpha = 0.2f), contentColor = colorScheme.secondary),
                    border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.secondary)
                ) {
                    Icon(Icons.Outlined.NotificationsActive, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Simular Timbre Tuya en Pantalla", fontWeight = FontWeight.SemiBold)
                }
            }
        }

        // Modo de Enlace
        Card(
            colors = CardDefaults.cardColors(containerColor = colorScheme.surface),
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Modo de Enlace", fontWeight = FontWeight.Bold, color = colorScheme.onSurface)

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = { onToggleMode(false) },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (!uiState.useRemote) colorScheme.primary else colorScheme.surfaceVariant,
                            contentColor = if (!uiState.useRemote) colorScheme.onPrimary else colorScheme.onSurface
                        )
                    ) {
                        Text("WiFi Local", fontWeight = FontWeight.SemiBold)
                    }

                    Button(
                        onClick = { onToggleMode(true) },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (uiState.useRemote) colorScheme.primary else colorScheme.surfaceVariant,
                            contentColor = if (uiState.useRemote) colorScheme.onPrimary else colorScheme.onSurface
                        )
                    ) {
                        Text("Cloudflare", fontWeight = FontWeight.SemiBold)
                    }
                }

                OutlinedButton(
                    onClick = onOpenConfig,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = colorScheme.onSurface),
                    border = androidx.compose.foundation.BorderStroke(1.dp, colorScheme.outline)
                ) {
                    Icon(Icons.Outlined.Edit, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Configurar URLs de Conexión")
                }
            }
        }
    }
}

@Composable
fun UrlConfigDialog(
    remoteUrl: String,
    localUrl: String,
    useRemote: Boolean,
    onDismiss: () -> Unit,
    onSave: (String, String, Boolean) -> Unit
) {
    var remote by remember { mutableStateOf(remoteUrl) }
    var local by remember { mutableStateOf(localUrl) }
    var isRemoteSelected by remember { mutableStateOf(useRemote) }
    val colorScheme = MaterialTheme.colorScheme

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = colorScheme.surface,
        title = { Text("Configuración de Red Domos", color = colorScheme.primary, fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("URL Remota (Cloudflare Tunnel):", color = colorScheme.onSurfaceVariant, fontSize = 12.sp)
                OutlinedTextField(
                    value = remote,
                    onValueChange = { remote = it },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = colorScheme.primary,
                        unfocusedBorderColor = colorScheme.outline,
                        focusedTextColor = colorScheme.onSurface,
                        unfocusedTextColor = colorScheme.onSurface
                    )
                )

                Text("URL Local (IP en casa):", color = colorScheme.onSurfaceVariant, fontSize = 12.sp)
                OutlinedTextField(
                    value = local,
                    onValueChange = { local = it },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = colorScheme.primary,
                        unfocusedBorderColor = colorScheme.outline,
                        focusedTextColor = colorScheme.onSurface,
                        unfocusedTextColor = colorScheme.onSurface
                    )
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { onSave(remote, local, isRemoteSelected) },
                colors = ButtonDefaults.buttonColors(containerColor = colorScheme.primary, contentColor = colorScheme.onPrimary)
            ) {
                Text("Guardar", fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancelar", color = colorScheme.onSurfaceVariant)
            }
        }
    )
}
