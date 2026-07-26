package org.zuschnitt

import android.content.Context
import android.content.SharedPreferences
import androidx.compose.runtime.*
import org.json.JSONArray
import org.json.JSONObject

/** App-wide settings persisted in SharedPreferences. */
data class AppSettings(
    val kerf: Float = 3.0f,
    val defaultSheetWidth: Float = 2440f,
    val defaultSheetHeight: Float = 1220f,
)

/** Centralised mutable state for the whole app. */
class AppState(context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("zuschnitt", Context.MODE_PRIVATE)

    var sheets by mutableStateOf(mutableListOf<Sheet>())
    var pieces by mutableStateOf(mutableListOf<Piece>())
    var resultText by mutableStateOf("")
    var currentFilePath by mutableStateOf<String?>(null)

    var settings by mutableStateOf(loadSettings())

    // Recent files: list of absolute path strings (max 5)
    var recentFiles by mutableStateOf(loadRecent())

    // ── Settings ──────────────────────────────────────────────────────────

    private fun loadSettings() = AppSettings(
        kerf = prefs.getFloat("kerf", 3.0f),
        defaultSheetWidth = prefs.getFloat("default_sheet_width", 2440f),
        defaultSheetHeight = prefs.getFloat("default_sheet_height", 1220f),
    )

    fun saveSettings(s: AppSettings) {
        settings = s
        prefs.edit()
            .putFloat("kerf", s.kerf)
            .putFloat("default_sheet_width", s.defaultSheetWidth)
            .putFloat("default_sheet_height", s.defaultSheetHeight)
            .apply()
    }

    // ── Recent files ──────────────────────────────────────────────────────

    private fun loadRecent(): List<String> {
        val json = prefs.getString("recent_files", "[]") ?: "[]"
        return try {
            val arr = JSONArray(json)
            (0 until arr.length()).map { arr.getString(it) }
        } catch (_: Exception) { emptyList() }
    }

    fun addRecent(path: String) {
        val updated = (listOf(path) + recentFiles.filter { it != path }).take(5)
        recentFiles = updated
        prefs.edit()
            .putString("recent_files", JSONArray(updated).toString())
            .apply()
    }

    fun removeRecent(path: String) {
        val updated = recentFiles.filter { it != path }
        recentFiles = updated
        prefs.edit()
            .putString("recent_files", JSONArray(updated).toString())
            .apply()
    }

    // ── Serialisation (.zusc JSON) ────────────────────────────────────────

    fun toJson(): String {
        val obj = JSONObject()
        val sheetsArr = JSONArray()
        sheets.forEach { s ->
            sheetsArr.put(JSONObject().apply {
                put("width", s.width)
                put("height", s.height)
                put("quantity", s.quantity)
            })
        }
        val piecesArr = JSONArray()
        pieces.forEach { p ->
            piecesArr.put(JSONObject().apply {
                put("width", p.width)
                put("height", p.height)
                put("quantity", p.quantity)
                put("can_rotate", p.canRotate)
            })
        }
        obj.put("sheets", sheetsArr)
        obj.put("pieces", piecesArr)
        obj.put("kerf", settings.kerf)
        return obj.toString(2)
    }

    fun fromJson(json: String) {
        val obj = JSONObject(json)
        sheets = (0 until obj.getJSONArray("sheets").length()).map { i ->
            val s = obj.getJSONArray("sheets").getJSONObject(i)
            Sheet(s.getDouble("width").toFloat(), s.getDouble("height").toFloat(), s.getInt("quantity"))
        }.toMutableList()
        pieces = (0 until obj.getJSONArray("pieces").length()).map { i ->
            val p = obj.getJSONArray("pieces").getJSONObject(i)
            Piece(
                p.getDouble("width").toFloat(),
                p.getDouble("height").toFloat(),
                p.getInt("quantity"),
                p.optBoolean("can_rotate", true)
            )
        }.toMutableList()
        if (obj.has("kerf")) {
            settings = settings.copy(kerf = obj.getDouble("kerf").toFloat())
        }
    }
}
