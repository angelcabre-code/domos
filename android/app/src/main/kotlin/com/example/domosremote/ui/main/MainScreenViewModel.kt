package com.example.domosremote.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.domosremote.data.CalendarEvent
import com.example.domosremote.data.DomosApiClient
import com.example.domosremote.data.HomeIncident
import com.example.domosremote.data.KioskStatus
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class DomosUiState(
    val status: KioskStatus = KioskStatus(),
    val incidents: List<HomeIncident> = emptyList(),
    val calendarEvents: List<CalendarEvent> = emptyList(),
    val isSendingMessage: Boolean = false,
    val messageFeedback: String? = null,
    val isSuccessMessage: Boolean = true,
    val activeTab: Int = 0, // 0: Kiosko WebView, 1: Mensajes, 2: Incidencias & Casa, 3: Control
    val useRemote: Boolean = true,
    val remoteUrl: String = DomosApiClient.baseUrl,
    val localUrl: String = DomosApiClient.localUrl,
    val isDarkTheme: Boolean = false // Modo Claro por defecto
)

class MainScreenViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(DomosUiState())
    val uiState: StateFlow<DomosUiState> = _uiState.asStateFlow()

    init {
        autoDetectAndRefresh()
    }

    fun toggleTheme() {
        _uiState.value = _uiState.value.copy(isDarkTheme = !_uiState.value.isDarkTheme)
    }

    fun setTheme(dark: Boolean) {
        _uiState.value = _uiState.value.copy(isDarkTheme = dark)
    }

    fun setTab(index: Int) {
        _uiState.value = _uiState.value.copy(activeTab = index)
    }

    fun toggleConnectionMode(remote: Boolean) {
        DomosApiClient.useRemote = remote
        _uiState.value = _uiState.value.copy(useRemote = remote)
        refreshAll()
    }

    fun updateUrls(remote: String, local: String) {
        DomosApiClient.baseUrl = remote
        DomosApiClient.localUrl = local
        _uiState.value = _uiState.value.copy(remoteUrl = remote, localUrl = local)
        refreshAll()
    }

    fun autoDetectAndRefresh() {
        viewModelScope.launch {
            val remote = DomosApiClient.autoSelectConnection()
            _uiState.value = _uiState.value.copy(useRemote = remote)
            refreshAll()
        }
    }

    fun refreshAll() {
        refreshStatus()
        fetchIncidents()
        fetchCalendar()
    }

    fun refreshStatus() {
        viewModelScope.launch {
            val res = DomosApiClient.getStatus()
            res.onSuccess {
                _uiState.value = _uiState.value.copy(status = it)
            }.onFailure {
                val remote = DomosApiClient.autoSelectConnection()
                if (remote != _uiState.value.useRemote) {
                    _uiState.value = _uiState.value.copy(useRemote = remote)
                    val retry = DomosApiClient.getStatus()
                    retry.onSuccess {
                        _uiState.value = _uiState.value.copy(status = it)
                        return@launch
                    }
                }
                _uiState.value = _uiState.value.copy(
                    status = _uiState.value.status.copy(isOnline = false)
                )
            }
        }
    }

    fun fetchIncidents() {
        viewModelScope.launch {
            val res = DomosApiClient.getIncidents()
            res.onSuccess { list ->
                _uiState.value = _uiState.value.copy(incidents = list)
            }
        }
    }

    fun fetchCalendar() {
        viewModelScope.launch {
            val res = DomosApiClient.getCalendar()
            res.onSuccess { list ->
                _uiState.value = _uiState.value.copy(calendarEvents = list)
            }
        }
    }

    fun resolveIncident(id: String) {
        viewModelScope.launch {
            DomosApiClient.resolveIncident(id)
            fetchIncidents()
        }
    }

    fun sendFamilyMessage(sender: String, text: String, speak: Boolean) {
        if (text.isBlank()) return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSendingMessage = true, messageFeedback = null)
            val res = DomosApiClient.sendMessage(sender, text, speak)
            res.onSuccess {
                _uiState.value = _uiState.value.copy(
                    isSendingMessage = false,
                    messageFeedback = "¡Mensaje emitido en la pantalla de Domos!",
                    isSuccessMessage = true
                )
            }.onFailure { err ->
                _uiState.value = _uiState.value.copy(
                    isSendingMessage = false,
                    messageFeedback = "Error de envío: ${err.message}",
                    isSuccessMessage = false
                )
            }
            delay(4000)
            _uiState.value = _uiState.value.copy(messageFeedback = null)
        }
    }

    fun setBrightness(pct: Int) {
        viewModelScope.launch {
            DomosApiClient.setBrightness(pct)
            refreshStatus()
        }
    }

    fun triggerDoorbell() {
        viewModelScope.launch {
            DomosApiClient.triggerDoorbell("¡Alerta Videoportero Tuya (Remoto)!")
        }
    }
}
