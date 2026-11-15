package com.example.domosremote.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val DomosLightColorScheme = lightColorScheme(
    primary = LightCyan,
    onPrimary = Color.White,
    primaryContainer = LightSurfaceVariant,
    onPrimaryContainer = LightCyan,
    secondary = LightGreen,
    onSecondary = Color.White,
    tertiary = LightAmber,
    error = LightCoral,
    background = LightBg,
    onBackground = LightTextPrimary,
    surface = LightSurface,
    onSurface = LightTextPrimary,
    surfaceVariant = LightSurfaceVariant,
    onSurfaceVariant = LightTextSecondary,
    outline = LightBorder
)

val DomosDarkColorScheme = darkColorScheme(
    primary = NeonCyan,
    onPrimary = CyberDark,
    primaryContainer = CyberSurfaceVariant,
    onPrimaryContainer = NeonCyan,
    secondary = NeonGreen,
    onSecondary = CyberDark,
    tertiary = NeonAmber,
    error = NeonCoral,
    background = CyberDark,
    onBackground = TextPrimaryDark,
    surface = CyberSurface,
    onSurface = TextPrimaryDark,
    surfaceVariant = CyberSurfaceVariant,
    onSurfaceVariant = TextSecondaryDark,
    outline = CyberBorder
)

@Composable
fun DomosRemoteTheme(
    darkTheme: Boolean = false, // Modo Claro por defecto
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DomosDarkColorScheme else DomosLightColorScheme
    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
