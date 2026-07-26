package org.zuschnitt

import android.content.ContentValues
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.pdf.PdfDocument
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStream

/** Result data passed from Python bridge for rendering. */
data class PlacedRect(
    val x: Float, val y: Float,
    val w: Float, val h: Float,
    val label: String,
    val color: Int,
)

data class SheetResult(
    val sheetW: Float,
    val sheetH: Float,
    val placements: List<PlacedRect>,
    val efficiency: Float,
)

// ── PDF ───────────────────────────────────────────────────────────────────

fun exportPdf(context: Context, layouts: List<SheetResult>, projectName: String): String {
    val doc = PdfDocument()
    val scale = 0.3f  // mm → points (rough: 1 pt ≈ 0.353 mm → scale≈2.83, but let's fit to A4)

    layouts.forEachIndexed { idx, layout ->
        // Fit sheet into A4 landscape (842 × 595 pts)
        val pageW = 842
        val pageH = 595
        val sx = (pageW - 40) / layout.sheetW
        val sy = (pageH - 80) / layout.sheetH
        val s = minOf(sx, sy)

        val pageInfo = PdfDocument.PageInfo.Builder(pageW, pageH, idx + 1).create()
        val page = doc.startPage(pageInfo)
        val c: Canvas = page.canvas

        val marginLeft = 20f
        val marginTop = 60f

        // Title
        val titlePaint = Paint().apply {
            color = Color.BLACK
            textSize = 14f
            isFakeBoldText = true
        }
        c.drawText(
            "Sheet ${idx + 1} — ${layout.sheetW.toInt()}×${layout.sheetH.toInt()} mm  " +
            "Efficiency: ${"%.1f".format(layout.efficiency)}%",
            marginLeft, 40f, titlePaint
        )

        // Sheet border
        val borderPaint = Paint().apply {
            color = Color.BLACK
            style = Paint.Style.STROKE
            strokeWidth = 1.5f
        }
        c.drawRect(
            marginLeft,
            marginTop,
            marginLeft + layout.sheetW * s,
            marginTop + layout.sheetH * s,
            borderPaint
        )

        // Pieces
        val fillPaint = Paint().apply { style = Paint.Style.FILL }
        val strokePaint = Paint().apply {
            style = Paint.Style.STROKE
            strokeWidth = 0.8f
            color = Color.DKGRAY
        }
        val textPaint = Paint().apply {
            color = Color.BLACK
            textSize = 8f
        }

        layout.placements.forEachIndexed { i, rect ->
            val left = marginLeft + rect.x * s
            val top = marginTop + rect.y * s
            val right = left + rect.w * s
            val bottom = top + rect.h * s

            fillPaint.color = rect.color
            c.drawRect(left, top, right, bottom, fillPaint)
            c.drawRect(left, top, right, bottom, strokePaint)
            c.drawText(rect.label, left + 3, top + 12, textPaint)
            c.drawText("${rect.w.toInt()}×${rect.h.toInt()}", left + 3, top + 22, textPaint)
        }

        doc.finishPage(page)
    }

    val fileName = "${projectName.ifBlank { "zuschnitt" }}-plan.pdf"
    return writeToDownloads(context, fileName, "application/pdf") { out ->
        doc.writeTo(out)
    }.also { doc.close() }
}

// ── SVG ───────────────────────────────────────────────────────────────────

fun exportSvg(context: Context, layouts: List<SheetResult>, projectName: String): String {
    val sb = StringBuilder()
    val padding = 20
    val labelHeight = 30
    val gap = 20

    // Calculate total SVG height
    val totalH = layouts.sumOf { (it.sheetH + labelHeight + gap).toDouble() }.toInt() + padding * 2
    val maxW = (layouts.maxOfOrNull { it.sheetW } ?: 0f).toInt() + padding * 2

    sb.appendLine("""<?xml version="1.0" encoding="UTF-8"?>""")
    sb.appendLine("""<svg xmlns="http://www.w3.org/2000/svg" width="$maxW" height="$totalH">""")
    sb.appendLine("""  <rect width="100%" height="100%" fill="white"/>""")

    var offsetY = padding.toFloat()
    layouts.forEachIndexed { idx, layout ->
        val x = padding.toFloat()

        // Label
        sb.appendLine(
            """  <text x="$x" y="${offsetY + 16}" font-size="14" font-weight="bold" fill="black">""" +
            """Sheet ${idx + 1} — ${layout.sheetW.toInt()}×${layout.sheetH.toInt()} mm""" +
            """  (${"%.1f".format(layout.efficiency)}% used)</text>"""
        )
        offsetY += labelHeight

        // Sheet border
        sb.appendLine(
            """  <rect x="$x" y="$offsetY" width="${layout.sheetW}" height="${layout.sheetH}" """ +
            """fill="none" stroke="black" stroke-width="2"/>"""
        )

        // Pieces
        layout.placements.forEachIndexed { i, rect ->
            val px = x + rect.x
            val py = offsetY + rect.y
            val hex = "#%06X".format(rect.color and 0xFFFFFF)
            sb.appendLine(
                """  <rect x="$px" y="$py" width="${rect.w}" height="${rect.h}" """ +
                """fill="$hex" fill-opacity="0.7" stroke="#444" stroke-width="0.5"/>"""
            )
            sb.appendLine(
                """  <text x="${px + 4}" y="${py + 14}" font-size="10" fill="black">""" +
                """${rect.label} ${rect.w.toInt()}×${rect.h.toInt()}</text>"""
            )
        }

        offsetY += layout.sheetH + gap
    }

    sb.appendLine("</svg>")

    val fileName = "${projectName.ifBlank { "zuschnitt" }}-plan.svg"
    return writeToDownloads(context, fileName, "image/svg+xml") { out ->
        out.write(sb.toString().toByteArray())
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────

private fun writeToDownloads(
    context: Context,
    fileName: String,
    mimeType: String,
    write: (OutputStream) -> Unit,
): String {
    return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
        val values = ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME, fileName)
            put(MediaStore.Downloads.MIME_TYPE, mimeType)
            put(MediaStore.Downloads.IS_PENDING, 1)
        }
        val resolver = context.contentResolver
        val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
            ?: error("MediaStore insert failed")
        resolver.openOutputStream(uri)!!.use { write(it) }
        values.clear()
        values.put(MediaStore.Downloads.IS_PENDING, 0)
        resolver.update(uri, values, null, null)
        "Saved to Downloads/$fileName"
    } else {
        val dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
        val file = File(dir, fileName)
        FileOutputStream(file).use { write(it) }
        "Saved to ${file.absolutePath}"
    }
}

// Pastel colour palette for pieces
private val PALETTE = listOf(
    0xFFAED6F1.toInt(), 0xFFA9DFBF.toInt(), 0xFFF9E79F.toInt(),
    0xFFF1948A.toInt(), 0xFFD7BDE2.toInt(), 0xFFA3E4D7.toInt(),
    0xFFFAD7A0.toInt(), 0xFFABB2B9.toInt(), 0xFFD2B4DE.toInt(),
    0xFF82E0AA.toInt(),
)

fun paletteColor(idx: Int) = PALETTE[idx % PALETTE.size]
