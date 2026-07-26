package org.zuschnitt

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp

@Composable
fun SettingsDialog(
    settings: AppSettings,
    onConfirm: (AppSettings) -> Unit,
    onDismiss: () -> Unit,
) {
    var kerfText by remember { mutableStateOf(settings.kerf.toString()) }
    var defWidthText by remember { mutableStateOf(settings.defaultSheetWidth.toInt().toString()) }
    var defHeightText by remember { mutableStateOf(settings.defaultSheetHeight.toInt().toString()) }

    val kerf = kerfText.toFloatOrNull()
    val defWidth = defWidthText.toFloatOrNull()
    val defHeight = defHeightText.toFloatOrNull()
    val valid = kerf != null && kerf >= 0 &&
                defWidth != null && defWidth > 0 &&
                defHeight != null && defHeight > 0

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Settings") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Cut Settings", style = MaterialTheme.typography.labelLarge)
                OutlinedTextField(
                    value = kerfText,
                    onValueChange = { kerfText = it },
                    label = { Text("Kerf (saw blade width, mm)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    singleLine = true,
                    isError = kerf == null || kerf < 0,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(4.dp))
                Text("Default Stock Sheet Size", style = MaterialTheme.typography.labelLarge)
                OutlinedTextField(
                    value = defWidthText,
                    onValueChange = { defWidthText = it },
                    label = { Text("Width (mm)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    isError = defWidth == null || defWidth <= 0,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = defHeightText,
                    onValueChange = { defHeightText = it },
                    label = { Text("Height (mm)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    isError = defHeight == null || defHeight <= 0,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    onConfirm(AppSettings(kerf!!, defWidth!!, defHeight!!))
                },
                enabled = valid
            ) { Text("Save") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}
