package org.zuschnitt

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Initialize Python
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
    var sheets by remember { mutableStateOf(listOf(Sheet(1000f, 500f, 1))) }
    var pieces by remember { mutableStateOf(listOf(Piece(400f, 300f, 1))) }
    var resultText by remember { mutableStateOf("") }
    
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
                onClick = {
                    resultText = runOptimizer(sheets, pieces)
                }
            ) {
                Icon(Icons.Filled.Add, "Optimize")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                Text(
                    "Stock Sheets",
                    style = MaterialTheme.typography.titleMedium
                )
            }
            
            items(sheets) { sheet ->
                SheetCard(sheet)
            }
            
            item {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "Pieces to Cut",
                    style = MaterialTheme.typography.titleMedium
                )
            }
            
            items(pieces) { piece ->
                PieceCard(piece)
            }
            
            if (resultText.isNotEmpty()) {
                item {
                    Spacer(modifier = Modifier.height(8.dp))
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
fun SheetCard(sheet: Sheet) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text("${sheet.width.toInt()} × ${sheet.height.toInt()} mm")
            Spacer(modifier = Modifier.weight(1f))
            Text("Qty: ${sheet.quantity}")
        }
    }
}

@Composable
fun PieceCard(piece: Piece) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text("${piece.width.toInt()} × ${piece.height.toInt()} mm")
            Spacer(modifier = Modifier.weight(1f))
            Text("Qty: ${piece.quantity}")
        }
    }
}

fun runOptimizer(sheets: List<Sheet>, pieces: List<Piece>): String {
    return try {
        val py = Python.getInstance()
        val module = py.getModule("zuschnitt.optimizer_2d")
        
        // Create Python lists
        val pySheets = py.getBuiltins().callAttr(
            "list",
            sheets.map { mapOf(
                "width" to it.width,
                "height" to it.height,
                "quantity" to it.quantity
            )}
        )
        
        val pyPieces = py.getBuiltins().callAttr(
            "list",
            pieces.map { mapOf(
                "width" to it.width,
                "height" to it.height,
                "quantity" to it.quantity
            )}
        )
        
        // Call optimizer
        val result = module.callAttr("optimize_simple", pySheets, pyPieces)
        
        "Optimization complete!\n${result.toString()}"
    } catch (e: Exception) {
        "Error: ${e.message}"
    }
}

data class Sheet(val width: Float, val height: Float, val quantity: Int)
data class Piece(val width: Float, val height: Float, val quantity: Int)
