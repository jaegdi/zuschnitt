package org.zuschnitt

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class Sheet(val width: Float, val height: Float, val quantity: Int)
data class Piece(val width: Float, val height: Float, val quantity: Int)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        enableEdgeToEdge()
        setContent {
            ZuschnittTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val appState = remember { AppState(this) }
                    ZuschnittApp(appState)
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ZuschnittApp(appState: AppState) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    // Last optimizer layouts (for export)
    var lastLayouts by remember { mutableStateOf<List<SheetResult>>(emptyList()) }

    // Dialog visibility flags
    var sheetDialogIndex by remember { mutableStateOf<Int?>(null) }
    var pieceDialogIndex by remember { mutableStateOf<Int?>(null) }
    var showSettings by remember { mutableStateOf(false) }
    var showRecentMenu by remember { mutableStateOf(false) }
    var menuExpanded by remember { mutableStateOf(false) }
    var statusMessage by remember { mutableStateOf("") }

    // File pickers
    val createFileLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/json")
    ) { uri ->
        if (uri != null) {
            scope.launch(Dispatchers.IO) {
                try {
                    context.contentResolver.openOutputStream(uri)?.use {
                        it.write(appState.toJson().toByteArray())
                    }
                    val path = uri.toString()
                    withContext(Dispatchers.Main) {
                        appState.currentFilePath = path
                        appState.addRecent(path)
                        statusMessage = "Saved."
                    }
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) { statusMessage = "Save failed: ${e.message}" }
                }
            }
        }
    }

    val openFileLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            scope.launch(Dispatchers.IO) {
                try {
                    val json = context.contentResolver.openInputStream(uri)
                        ?.bufferedReader()?.readText() ?: ""
                    withContext(Dispatchers.Main) {
                        appState.fromJson(json)
                        val path = uri.toString()
                        appState.currentFilePath = path
                        appState.addRecent(path)
                        appState.resultText = ""
                        lastLayouts = emptyList()
                        statusMessage = "Opened."
                    }
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) { statusMessage = "Open failed: ${e.message}" }
                }
            }
        }
    }

    // Dialogs
    sheetDialogIndex?.let { idx ->
        val existing = if (idx >= 0) appState.sheets[idx] else null
        ItemDialog(
            title = if (existing == null) "Add Stock Sheet" else "Edit Stock Sheet",
            initialWidth = existing?.width ?: appState.settings.defaultSheetWidth,
            initialHeight = existing?.height ?: appState.settings.defaultSheetHeight,
            initialQty = existing?.quantity ?: 1,
            onConfirm = { w, h, qty ->
                appState.sheets = appState.sheets.toMutableList().also {
                    if (idx >= 0) it[idx] = Sheet(w, h, qty) else it.add(Sheet(w, h, qty))
                }
                sheetDialogIndex = null
            },
            onDismiss = { sheetDialogIndex = null }
        )
    }

    pieceDialogIndex?.let { idx ->
        val existing = if (idx >= 0) appState.pieces[idx] else null
        ItemDialog(
            title = if (existing == null) "Add Piece" else "Edit Piece",
            initialWidth = existing?.width ?: 200f,
            initialHeight = existing?.height ?: 100f,
            initialQty = existing?.quantity ?: 1,
            onConfirm = { w, h, qty ->
                appState.pieces = appState.pieces.toMutableList().also {
                    if (idx >= 0) it[idx] = Piece(w, h, qty) else it.add(Piece(w, h, qty))
                }
                pieceDialogIndex = null
            },
            onDismiss = { pieceDialogIndex = null }
        )
    }

    if (showSettings) {
        SettingsDialog(
            settings = appState.settings,
            onConfirm = { appState.saveSettings(it); showSettings = false },
            onDismiss = { showSettings = false }
        )
    }

    // Recent files sub-menu
    if (showRecentMenu) {
        AlertDialog(
            onDismissRequest = { showRecentMenu = false },
            title = { Text("Open Recent") },
            text = {
                if (appState.recentFiles.isEmpty()) {
                    Text("No recent files.")
                } else {
                    Column {
                        appState.recentFiles.forEach { path ->
                            val name = path.substringAfterLast('/').substringAfterLast('%')
                            TextButton(onClick = {
                                showRecentMenu = false
                                scope.launch(Dispatchers.IO) {
                                    try {
                                        val uri = Uri.parse(path)
                                        val json = context.contentResolver.openInputStream(uri)
                                            ?.bufferedReader()?.readText() ?: ""
                                        withContext(Dispatchers.Main) {
                                            appState.fromJson(json)
                                            appState.currentFilePath = path
                                            appState.resultText = ""
                                            lastLayouts = emptyList()
                                            statusMessage = "Opened."
                                        }
                                    } catch (e: Exception) {
                                        withContext(Dispatchers.Main) {
                                            statusMessage = "Open failed: ${e.message}"
                                        }
                                    }
                                }
                            }) { Text(name) }
                        }
                    }
                }
            },
            confirmButton = { TextButton(onClick = { showRecentMenu = false }) { Text("Close") } }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        appState.currentFilePath
                            ?.substringAfterLast('/')?.substringAfterLast('%')
                            ?.removeSuffix(".zusc")
                            ?.removeSuffix(".json")
                            ?: "✂ Zuschnitt"
                    )
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                ),
                actions = {
                    // ⋮ overflow menu
                    IconButton(onClick = { menuExpanded = true }) {
                        Icon(Icons.Filled.MoreVert, contentDescription = "Menu")
                    }
                    DropdownMenu(
                        expanded = menuExpanded,
                        onDismissRequest = { menuExpanded = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("New") },
                            onClick = {
                                menuExpanded = false
                                appState.sheets = mutableListOf()
                                appState.pieces = mutableListOf()
                                appState.resultText = ""
                                appState.currentFilePath = null
                                lastLayouts = emptyList()
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Open…") },
                            onClick = {
                                menuExpanded = false
                                openFileLauncher.launch(arrayOf("application/json", "*/*"))
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Open Recent") },
                            onClick = { menuExpanded = false; showRecentMenu = true }
                        )
                        DropdownMenuItem(
                            text = { Text("Save") },
                            onClick = {
                                menuExpanded = false
                                val path = appState.currentFilePath
                                if (path != null) {
                                    scope.launch(Dispatchers.IO) {
                                        try {
                                            context.contentResolver
                                                .openOutputStream(Uri.parse(path), "wt")
                                                ?.use { it.write(appState.toJson().toByteArray()) }
                                            withContext(Dispatchers.Main) { statusMessage = "Saved." }
                                        } catch (e: Exception) {
                                            withContext(Dispatchers.Main) {
                                                statusMessage = "Save failed: ${e.message}"
                                            }
                                        }
                                    }
                                } else {
                                    createFileLauncher.launch("project.zusc")
                                }
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Save As…") },
                            onClick = {
                                menuExpanded = false
                                createFileLauncher.launch("project.zusc")
                            }
                        )
                        HorizontalDivider()
                        DropdownMenuItem(
                            text = { Text("Export PDF") },
                            onClick = {
                                menuExpanded = false
                                if (lastLayouts.isEmpty()) {
                                    statusMessage = "Run the optimizer first (▶)."
                                } else {
                                    scope.launch(Dispatchers.IO) {
                                        val msg = try {
                                            exportPdf(context, lastLayouts,
                                                appState.currentFilePath
                                                    ?.substringAfterLast('/')
                                                    ?.removeSuffix(".zusc") ?: "zuschnitt")
                                        } catch (e: Exception) { "PDF failed: ${e.message}" }
                                        withContext(Dispatchers.Main) { statusMessage = msg }
                                    }
                                }
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Export SVG") },
                            onClick = {
                                menuExpanded = false
                                if (lastLayouts.isEmpty()) {
                                    statusMessage = "Run the optimizer first (▶)."
                                } else {
                                    scope.launch(Dispatchers.IO) {
                                        val msg = try {
                                            exportSvg(context, lastLayouts,
                                                appState.currentFilePath
                                                    ?.substringAfterLast('/')
                                                    ?.removeSuffix(".zusc") ?: "zuschnitt")
                                        } catch (e: Exception) { "SVG failed: ${e.message}" }
                                        withContext(Dispatchers.Main) { statusMessage = msg }
                                    }
                                }
                            }
                        )
                        HorizontalDivider()
                        DropdownMenuItem(
                            text = { Text("Settings…") },
                            onClick = { menuExpanded = false; showSettings = true }
                        )
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = {
                    scope.launch(Dispatchers.Default) {
                        val (text, layouts) = runOptimizer(
                            appState.sheets, appState.pieces, appState.settings.kerf
                        )
                        withContext(Dispatchers.Main) {
                            appState.resultText = text
                            lastLayouts = layouts
                        }
                    }
                }
            ) {
                Icon(Icons.Filled.PlayArrow, contentDescription = "Optimize")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(vertical = 16.dp)
        ) {
            // Status / result banner
            if (statusMessage.isNotEmpty() || appState.resultText.isNotEmpty()) {
                item {
                    val msg = appState.resultText.ifEmpty { statusMessage }
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.secondaryContainer
                        )
                    ) {
                        Text(
                            text = msg,
                            modifier = Modifier.padding(12.dp),
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                }
            }

            // Stock Sheets
            item { SectionHeader("Stock Sheets", onAdd = { sheetDialogIndex = -1 }) }
            itemsIndexed(appState.sheets) { idx, sheet ->
                ItemCard(
                    label = "${sheet.width.toInt()} × ${sheet.height.toInt()} mm",
                    sublabel = "Qty: ${sheet.quantity}",
                    onClick = { sheetDialogIndex = idx },
                    onDelete = { appState.sheets = appState.sheets.toMutableList().also { it.removeAt(idx) } }
                )
            }

            // Pieces to Cut
            item { Spacer(Modifier.height(4.dp)); SectionHeader("Pieces to Cut", onAdd = { pieceDialogIndex = -1 }) }
            itemsIndexed(appState.pieces) { idx, piece ->
                ItemCard(
                    label = "${piece.width.toInt()} × ${piece.height.toInt()} mm",
                    sublabel = "Qty: ${piece.quantity}",
                    onClick = { pieceDialogIndex = idx },
                    onDelete = { appState.pieces = appState.pieces.toMutableList().also { it.removeAt(idx) } }
                )
            }
        }
    }
}

@Composable
fun SectionHeader(title: String, onAdd: () -> Unit) {
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
        IconButton(onClick = onAdd) { Icon(Icons.Filled.Add, contentDescription = "Add") }
    }
}

@Composable
fun ItemCard(label: String, sublabel: String, onClick: () -> Unit, onDelete: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(label, style = MaterialTheme.typography.bodyLarge)
                Text(sublabel, style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            IconButton(onClick = onDelete) {
                Icon(Icons.Filled.Delete, contentDescription = "Delete",
                    tint = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
fun ItemDialog(
    title: String,
    initialWidth: Float,
    initialHeight: Float,
    initialQty: Int,
    onConfirm: (Float, Float, Int) -> Unit,
    onDismiss: () -> Unit,
) {
    var widthText by remember { mutableStateOf(initialWidth.toInt().toString()) }
    var heightText by remember { mutableStateOf(initialHeight.toInt().toString()) }
    var qtyText by remember { mutableStateOf(initialQty.toString()) }

    val w = widthText.toFloatOrNull()
    val h = heightText.toFloatOrNull()
    val q = qtyText.toIntOrNull()
    val valid = w != null && w > 0 && h != null && h > 0 && q != null && q > 0

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = widthText, onValueChange = { widthText = it },
                    label = { Text("Width (mm)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true, isError = w == null || w <= 0,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = heightText, onValueChange = { heightText = it },
                    label = { Text("Height (mm)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true, isError = h == null || h <= 0,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = qtyText, onValueChange = { qtyText = it },
                    label = { Text("Quantity") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true, isError = q == null || q <= 0,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(w!!, h!!, q!!) }, enabled = valid) { Text("OK") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}

fun runOptimizer(
    sheets: List<Sheet>,
    pieces: List<Piece>,
    kerf: Float,
): Pair<String, List<SheetResult>> {
    return try {
        val py = Python.getInstance()
        val bridge = py.getModule("zuschnitt.android_bridge")

        val pySheets = sheets.map { mapOf("width" to it.width, "height" to it.height, "quantity" to it.quantity) }
        val pyPieces = pieces.map { mapOf("width" to it.width, "height" to it.height, "quantity" to it.quantity) }

        val result = bridge.callAttr("optimize_simple", pySheets, pyPieces, kerf).asMap()
        val success = result[PyObject.fromJava("success")]?.toBoolean() ?: false
        val layoutCount = result[PyObject.fromJava("layouts_count")]?.toInt() ?: 0
        val unplaced = result[PyObject.fromJava("unplaced_count")]?.toInt() ?: 0

        // Parse layout details for export
        val layouts = parseLayouts(result)

        val msg = if (success)
            "✅ $layoutCount sheet(s) used — all pieces placed."
        else
            "⚠️ $layoutCount sheet(s) used — $unplaced piece(s) could not be placed."

        Pair(msg, layouts)
    } catch (e: Exception) {
        Pair("❌ Error: ${e.message}", emptyList())
    }
}

private fun parseLayouts(result: Map<PyObject, PyObject>): List<SheetResult> {
    return try {
        val layoutsObj = result[PyObject.fromJava("layouts")] ?: return emptyList()
        layoutsObj.asList().mapIndexed { sheetIdx, layoutObj ->
            val lm = layoutObj.asMap()
            val sheetW = lm[PyObject.fromJava("sheet_width")]?.toFloat() ?: 0f
            val sheetH = lm[PyObject.fromJava("sheet_height")]?.toFloat() ?: 0f
            val efficiency = lm[PyObject.fromJava("efficiency")]?.toFloat() ?: 0f
            val placementsObj = lm[PyObject.fromJava("placements")]
            val placed = placementsObj?.asList()?.mapIndexed { i, p ->
                val pm = p.asMap()
                PlacedRect(
                    x = pm[PyObject.fromJava("x")]?.toFloat() ?: 0f,
                    y = pm[PyObject.fromJava("y")]?.toFloat() ?: 0f,
                    w = pm[PyObject.fromJava("placed_width")]?.toFloat() ?: 0f,
                    h = pm[PyObject.fromJava("placed_height")]?.toFloat() ?: 0f,
                    label = pm[PyObject.fromJava("label")]?.toString() ?: "P${i + 1}",
                    color = paletteColor(i),
                )
            } ?: emptyList()
            SheetResult(sheetW, sheetH, placed, efficiency)
        }
    } catch (_: Exception) { emptyList() }
}

