package com.example.domosremote.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

data class KioskStatus(
    val batteryPct: Int = 100,
    val batteryStatus: String = "Normal",
    val brightness: Int = 80,
    val isOnline: Boolean = false
)

data class HomeIncident(
    val id: String,
    val timestamp: String,
    val source: String,
    val severity: String,
    val title: String,
    val description: String,
    val resolved: Boolean
)

data class CalendarEvent(
    val id: String,
    val title: String,
    val date: String,
    val type: String,
    val reminderTime: String
)

object DomosApiClient {
    var baseUrl: String = "https://your-domos-tunnel.trycloudflare.com"
    var localUrl: String = "http://domos.local:8080"
    var useRemote: Boolean = true

    fun getActiveUrl(): String {
        return if (useRemote) baseUrl.trimEnd('/') else localUrl.trimEnd('/')
    }

    suspend fun autoSelectConnection(): Boolean = withContext(Dispatchers.IO) {
        val localReachable = try {
            val url = URL("${localUrl.trimEnd('/')}/api/status")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 900
                readTimeout = 900
                requestMethod = "GET"
            }
            val code = conn.responseCode
            conn.disconnect()
            code == 200
        } catch (_: Exception) {
            false
        }
        useRemote = !localReachable
        useRemote
    }

    suspend fun getStatus(): Result<KioskStatus> = withContext(Dispatchers.IO) {
        try {
            val url = URL("${getActiveUrl()}/api/status")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 4000
                readTimeout = 4000
                requestMethod = "GET"
            }
            if (conn.responseCode == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val json = JSONObject(reader.readText())
                reader.close()
                val bat = json.optJSONObject("battery")
                val cap = bat?.optInt("capacity", 100) ?: 100
                val st = bat?.optString("status", "Normal") ?: "Normal"
                val br = json.optInt("brightness", 80)
                Result.success(KioskStatus(cap, st, br, true))
            } else {
                Result.failure(Exception("HTTP ${conn.responseCode}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendTap(x: Float, y: Float): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val url = URL("${getActiveUrl()}/api/screen/tap")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 3000
                readTimeout = 3000
                requestMethod = "POST"
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            val payload = JSONObject().apply {
                put("x", x)
                put("y", y)
            }
            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(payload.toString())
            writer.flush()
            writer.close()
            Result.success(conn.responseCode == 200)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendMessage(sender: String, text: String, speak: Boolean): Result<String> = withContext(Dispatchers.IO) {
        try {
            val url = URL("${getActiveUrl()}/api/message/send")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 5000
                readTimeout = 5000
                requestMethod = "POST"
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            val payload = JSONObject().apply {
                put("sender", sender)
                put("text", text)
                put("speak", speak)
            }
            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(payload.toString())
            writer.flush()
            writer.close()

            if (conn.responseCode == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                reader.readText()
                reader.close()
                Result.success("Mensaje emitido en la pantalla de Domos")
            } else {
                Result.failure(Exception("HTTP Error: ${conn.responseCode}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun setBrightness(pct: Int): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val url = URL("${getActiveUrl()}/api/brightness")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 4000
                readTimeout = 4000
                requestMethod = "POST"
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            val payload = JSONObject().apply { put("brightness", pct) }
            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(payload.toString())
            writer.flush()
            writer.close()
            Result.success(conn.responseCode == 200)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun triggerDoorbell(title: String): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val url = URL("${getActiveUrl()}/api/doorbell/trigger")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 4000
                readTimeout = 4000
                requestMethod = "POST"
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            val payload = JSONObject().apply {
                put("title", title)
                put("stream_url", "")
            }
            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(payload.toString())
            writer.flush()
            writer.close()
            Result.success(conn.responseCode == 200)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getIncidents(): Result<List<HomeIncident>> = withContext(Dispatchers.IO) {
        try {
            val url = URL("${getActiveUrl()}/api/incidents")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 4000
                readTimeout = 4000
                requestMethod = "GET"
            }
            if (conn.responseCode == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val arr = JSONArray(reader.readText())
                reader.close()
                val list = mutableListOf<HomeIncident>()
                for (i in 0 until arr.length()) {
                    val obj = arr.getJSONObject(i)
                    list.add(
                        HomeIncident(
                            id = obj.optString("id"),
                            timestamp = obj.optString("timestamp"),
                            source = obj.optString("source"),
                            severity = obj.optString("severity", "info"),
                            title = obj.optString("title"),
                            description = obj.optString("description"),
                            resolved = obj.optBoolean("resolved", false)
                        )
                    )
                }
                Result.success(list)
            } else {
                Result.failure(Exception("HTTP ${conn.responseCode}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun resolveIncident(id: String): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val url = URL("${getActiveUrl()}/api/incidents/resolve")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 4000
                readTimeout = 4000
                requestMethod = "POST"
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            val payload = JSONObject().apply { put("id", id) }
            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(payload.toString())
            writer.flush()
            writer.close()
            Result.success(conn.responseCode == 200)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getCalendar(): Result<List<CalendarEvent>> = withContext(Dispatchers.IO) {
        try {
            val url = URL("${getActiveUrl()}/api/calendar")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 4000
                readTimeout = 4000
                requestMethod = "GET"
            }
            if (conn.responseCode == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val arr = JSONArray(reader.readText())
                reader.close()
                val list = mutableListOf<CalendarEvent>()
                for (i in 0 until arr.length()) {
                    val obj = arr.getJSONObject(i)
                    list.add(
                        CalendarEvent(
                            id = obj.optString("id"),
                            title = obj.optString("title"),
                            date = obj.optString("date"),
                            type = obj.optString("type", "event"),
                            reminderTime = obj.optString("reminder_time", "09:00")
                        )
                    )
                }
                Result.success(list)
            } else {
                Result.failure(Exception("HTTP ${conn.responseCode}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
