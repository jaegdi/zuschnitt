package org.zuschnitt

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Compose colours for the palette (must match ExportManager.paletteColor). */
private val COMPOSE_PALETTE = listOf(
    Color(0xFFAED6F1), Color(0xFFA9DFBF), Color(0xFFF9E79F),
    Color(0xFFF1948A), Color(0xFFD7BDE2), Color(0xFFA3E4D7),
    Color(0xFFFAD7A0), Color(0xFFABB2B9), Color(0xFFD2B4DE),
    Color(0xFF82E0AA),
)

fun composeColor(idx: Int): Color = COMPOSE_PALETTE[idx % COMPOSE_PALETTE.size]

/**
 * Renders one [SheetResult] as a scaled Canvas drawing showing all placed pieces.
 *
 * @param canvasWidthDp  Available width in dp — the sheet is scaled to fit.
 */
@Composable
fun SheetCanvas(layout: SheetResult, modifier: Modifier = Modifier) {
    val textMeasurer = rememberTextMeasurer()
    val labelStyle = TextStyle(fontSize = 9.sp, color = Color.Black)

    // Reserve some dp for the canvas height proportional to the sheet aspect ratio
    val aspectRatio = layout.sheetH / layout.sheetW.coerceAtLeast(1f)

    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(1f / aspectRatio.coerceIn(0.2f, 5f))
            .background(Color(0xFFF5F5F5))
    ) {
        val sx = size.width / layout.sheetW
        val sy = size.height / layout.sheetH
        val scale = minOf(sx, sy)

        // Sheet background
        drawRect(
            color = Color(0xFFECF0F1),
            size = Size(layout.sheetW * scale, layout.sheetH * scale)
        )
        // Sheet border
        drawRect(
            color = Color(0xFF2C3E50),
            size = Size(layout.sheetW * scale, layout.sheetH * scale),
            style = Stroke(width = 2f)
        )

        // Pieces
        layout.placements.forEachIndexed { i, rect ->
            val fill = composeColor(i)
            val left = rect.x * scale
            val top = rect.y * scale
            val w = rect.w * scale
            val h = rect.h * scale

            drawRect(color = fill, topLeft = Offset(left, top), size = Size(w, h))
            drawRect(
                color = Color(0xFF444444),
                topLeft = Offset(left, top),
                size = Size(w, h),
                style = Stroke(width = 0.8f)
            )

            // Label — only if piece is large enough to show text
            if (w > 30f && h > 18f) {
                val labelText = "${rect.w.toInt()}×${rect.h.toInt()}"
                val measured = textMeasurer.measure(labelText, labelStyle)
                val tx = left + (w - measured.size.width) / 2f
                val ty = top + (h - measured.size.height) / 2f
                drawText(measured, topLeft = Offset(tx.coerceAtLeast(left + 2), ty.coerceAtLeast(top + 2)))
            }
        }
    }
}

/**
 * Card wrapping [SheetCanvas] with a title row showing sheet number and efficiency.
 */
@Composable
fun SheetResultCard(sheetIndex: Int, layout: SheetResult) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(modifier = Modifier.fillMaxWidth()) {
                Text(
                    text = "Sheet ${sheetIndex + 1}  —  ${layout.sheetW.toInt()} × ${layout.sheetH.toInt()} mm",
                    style = MaterialTheme.typography.titleSmall,
                    modifier = Modifier.weight(1f)
                )
                Text(
                    text = "${"%.1f".format(layout.efficiency)}% used",
                    style = MaterialTheme.typography.labelMedium,
                    color = if (layout.efficiency >= 80f)
                        MaterialTheme.colorScheme.primary
                    else
                        MaterialTheme.colorScheme.error
                )
            }
            Spacer(Modifier.height(8.dp))
            SheetCanvas(layout)
            Spacer(Modifier.height(4.dp))
            Text(
                text = "${layout.placements.size} piece(s)  |  " +
                       "waste: ${"%.0f".format(layout.sheetW * layout.sheetH * (1 - layout.efficiency / 100))} mm²",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
