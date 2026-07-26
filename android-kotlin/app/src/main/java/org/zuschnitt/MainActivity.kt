package org.zuschnitt

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

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
                    ZuschnittApp()
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ZuschnittApp() {
    var sheets by remember { mutableStateOf(mutableListOf(Sheet(2440f, 1220f, 1))) }
    var pieces by remember { mutableStateOf(mutableListOf(Piece(400f, 300f, 2))) }
    var resultText by remember { mutableStateOf("") }

    // Dialog state: null = closed, -1 = new, >=0 = edit index
    var sheetDialogIndex by remember { mutableStateOf<Int?>(null) }
    var pieceDialogIndex by remember { mutableStateOf<Int?>(null) }

    // Show dialogs
    sheetDialogIndex?.let { idx ->
        val existing = if (idx >= 0) sheets[idx] else null
        ItemDialog(
            title = if (existing == null) "Add Stock Sheet" else "Edit Stock Sheet",
            initialWidth = existing?.width ?: 2440f,
            initialHeight = existing?.height ?: 1220f,
            initialQty = existing?.quantity ?: 1,
            onConfirm = { w, h, qty ->
                sheets = sheets.toMutableList().also {
                    if (idx >= 0) it[idx] = Sheet(w, h, qty)
                    else it.add(Sheet(w, h, qty))
                }
                sheetDialogIndex = null
            },
            onDismiss = { sheetDialogIndex = null }
        )
    }

    pieceDialogIndex?.let { idx ->
        val existing = if (idx >= 0) pieces[idx] else null
        ItemDialog(
            title = if (existing == null) "Add Piece" else "Edit Piece",
            initialWidth = existing?.width ?: 200f,
            initialHeight = existing?.height ?: 100f,
            initialQty = existing?.quantity ?: 1,
            onConfirm = { w, h, qty ->
                pieces = pieces.toMutableList().also {
                    if (idx >= 0) it[idx] = Piece(w, h, qty)
                    else it.add(Piece(w, h, qty))
                }
                pieceDialogIndex = null
            },
            onDismiss = { pieceDialogIndex = null }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("✂ Zuschnitt") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { resultText = runOptimizer(sheets, pieces) }
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
            // ── Stock Sheets ──────────────────────────────────────────
            item {
                SectionHeader(
                    title = "Stock Sheets",
                    onAdd = { sheetDialogIndex = -1 }
                )
            }
            itemsIndexed(sheets) { idx, sheet ->
                ItemCard(
                    label = "${sheet.width.toInt()} × ${sheet.height.toInt()} mm",
                    sublabel = "Qty: ${sheet.quantity}",
                    onClick = { sheetDialogIndex = idx },
                    onDelete = { sheets = sheets.toMutableList().also { it.removeAt(idx) } }
                )
            }

            // ── Pieces to Cut ─────────────────────────────────────────
            item {
                Spacer(Modifier.height(8.dp))
                SectionHeader(
                    title = "Pieces to Cut",
                    onAdd = { pieceDialogIndex = -1 }
                )
            }
            itemsIndexed(pieces) { idx, piece ->
                ItemCard(
                    label = "${piece.width.toInt()} × ${piece.height.toInt()} mm",
                    sublabel = "Qty: ${piece.quantity}",
                    onClick = { pieceDialogIndex = idx },
                    onDelete = { pieces = pieces.toMutableList().also { it.removeAt(idx) } }
                )
            }

            // ── Result ────────────────────────────────────────────────
            if (resultText.isNotEmpty()) {
                item {
                    Spacer(Modifier.height(8.dp))
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.secondaryContainer
                        )
                    ) {
                        Text(
                            text = resultText,
                            modifier = Modifier.padding(16.dp),
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SectionHeader(title: String, onAdd: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.weight(1f)
        )
        IconButton(onClick = onAdd) {
            Icon(Icons.Filled.Add, contentDescription = "Add $title")
        }
    }
}

@Composable
fun ItemCard(
    label: String,
    sublabel: String,
    onClick: () -> Unit,
    onDelete: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
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
                Icon(
                    Icons.Filled.Delete,
                    contentDescription = "Delete",
                    tint = MaterialTheme.colorScheme.error
                )
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
    onDismiss: () -> Unit
) {
    var widthText by remember { mutableStateOf(initialWidth.toInt().toString()) }
    var heightText by remember { mutableStateOf(initialHeight.toInt().toString()) }
    var qtyText by remember { mutableStateOf(initialQty.toString()) }

    val width = widthText.toFloatOrNull()
    val height = heightText.toFloatOrNull()
    val qty = qtyText.toIntOrNull()
    val valid = width != null && width > 0 && height != null && height > 0
            && qty != null && qty > 0

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = widthText,
                    onValueChange = { widthText = it },
                    label = { Text("Width (mm)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    isError = width == null || width <= 0,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = heightText,
                    onValueChange = { heightText = it },
                    label = { Text("Height (mm)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    isError = height == null || height <= 0,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = qtyText,
                    onValueChange = { qtyText = it },
                    label = { Text("Quantity") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    isError = qty == null || qty <= 0,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(width!!, height!!, qty!!) },
                enabled = valid
            ) { Text("OK") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

fun runOptimizer(sheets: List<Sheet>, pieces: List<Piece>): String {
    return try {
        val py = Python.getInstance()
        val bridge = py.getModule("zuschnitt.android_bridge")

        val pySheets = sheets.map { mapOf("width" to it.width, "height" to it.height, "quantity" to it.quantity) }
        val pyPieces = pieces.map { mapOf("width" to it.width, "height" to it.height, "quantity" to it.quantity) }

        val result = bridge.callAttr("optimize_simple", pySheets, pyPieces).asMap()

        val success = result[com.chaquo.python.PyObject.fromJava("success")]?.toBoolean() ?: false
        val layoutCount = result[com.chaquo.python.PyObject.fromJava("layouts_count")]?.toInt() ?: 0
        val unplaced = result[com.chaquo.python.PyObject.fromJava("unplaced_count")]?.toInt() ?: 0

        if (success) {
            "✅ Optimized: $layoutCount sheet(s) used, all pieces placed."
        } else {
            "⚠️ $layoutCount sheet(s) used, $unplaced piece(s) could not be placed."
        }
    } catch (e: Exception) {
        "❌ Error: ${e.message}"
    }
}
