package org.zuschnitt

import android.content.ContentValues
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.DashPathEffect
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.pdf.PdfDocument
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStream
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/** Result data passed from Python bridge for rendering. */
data class PlacedRect(
    val x: Float, val y: Float,
    val w: Float, val h: Float,
    val label: String,
    val color: Int,
)

data class CutLineData(
    val number: Int,
    val orientation: String,
    val position: Float,
)

data class SheetResult(
    val sheetW: Float,
    val sheetH: Float,
    val placements: List<PlacedRect>,
    val efficiency: Float,
    val cuts: List<CutLineData>,
)

private data class MarkerPlacement(
    val cut: CutLineData,
    val anchorX: Float,
    val anchorY: Float,
    val labelX: Float,
    val labelY: Float,
)

private fun spreadPositions(desired: List<Float>, minSep: Float): List<Float> {
    if (desired.isEmpty()) return emptyList()

    val clusters = mutableListOf(mutableListOf(desired.first()))
    for (pos in desired.drop(1)) {
        if (pos - clusters.last().last() < minSep) {
            clusters.last().add(pos)
        } else {
            clusters.add(mutableListOf(pos))
        }
    }

    val placed = mutableListOf<Float>()
    var prevEnd = Float.NEGATIVE_INFINITY
    for (cluster in clusters) {
        val count = cluster.size
        val center = cluster.sum() / count
        var start = center - (count - 1) * minSep / 2f
        start = max(start, prevEnd + minSep)
        repeat(count) { idx -> placed.add(start + idx * minSep) }
        prevEnd = placed.last()
    }
    return placed
}

private fun placeHorizontalMarkers(
    cuts: List<CutLineData>,
    anchorX: Float,
    labelX: Float,
    minSep: Float,
): List<MarkerPlacement> {
    val horizontal = cuts.filter { it.orientation == "H" }.sortedBy { it.position }
    val yPositions = spreadPositions(horizontal.map { it.position }, minSep)
    return horizontal.zip(yPositions).map { (cut, labelY) ->
        MarkerPlacement(cut, anchorX, cut.position, labelX, labelY)
    }
}

private fun placeVerticalMarkers(
    cuts: List<CutLineData>,
    anchorY: Float,
    labelY: Float,
    minSep: Float,
): List<MarkerPlacement> {
    val vertical = cuts.filter { it.orientation == "V" }.sortedBy { it.position }
    val xPositions = spreadPositions(vertical.map { it.position }, minSep)
    return vertical.zip(xPositions).map { (cut, labelX) ->
        MarkerPlacement(cut, cut.position, anchorY, labelX, labelY)
    }
}

private fun baseName(projectName: String): String =
    projectName.ifBlank { "cutting_plan" }

private fun drawCenteredText(canvas: Canvas, text: String, x: Float, y: Float, paint: Paint) {
    val bounds = Rect()
    paint.getTextBounds(text, 0, text.length, bounds)
    canvas.drawText(text, x - bounds.width() / 2f, y + bounds.height() / 2f, paint)
}

// ── PDF ───────────────────────────────────────────────────────────────────

fun exportPdf(context: Context, layouts: List<SheetResult>, projectName: String): String {
    val doc = PdfDocument()

    layouts.forEachIndexed { idx, layout ->
        val pageW = 842
        val pageH = 595
        val marginLeft = 20f
        val marginTop = 36f
        val dimLeft = 40f
        val dimTop = 34f
        val dimRight = 40f
        val dimBottom = 54f
        val drawW = pageW - marginLeft * 2 - dimLeft - dimRight
        val drawH = pageH - marginTop - 20f - dimTop - dimBottom
        val sx = drawW / layout.sheetW
        val sy = drawH / layout.sheetH
        val s = minOf(sx, sy)

        val pageInfo = PdfDocument.PageInfo.Builder(pageW, pageH, idx + 1).create()
        val page = doc.startPage(pageInfo)
        val c: Canvas = page.canvas

        val ox = marginLeft + dimLeft + (drawW - layout.sheetW * s) / 2f
        val oy = marginTop + dimTop + (drawH - layout.sheetH * s) / 2f

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
            ox,
            oy,
            ox + layout.sheetW * s,
            oy + layout.sheetH * s,
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
            val left = ox + rect.x * s
            val top = oy + rect.y * s
            val right = left + rect.w * s
            val bottom = top + rect.h * s

            fillPaint.color = rect.color
            c.drawRect(left, top, right, bottom, fillPaint)
            c.drawRect(left, top, right, bottom, strokePaint)
            c.drawText(rect.label, left + 3, top + 12, textPaint)
            c.drawText("${rect.w.toInt()}×${rect.h.toInt()}", left + 3, top + 22, textPaint)
        }

        val cutPaint = Paint().apply {
            color = Color.parseColor("#c0392b")
            style = Paint.Style.STROKE
            strokeWidth = 1.2f
            pathEffect = DashPathEffect(floatArrayOf(7f, 5f), 0f)
        }
        val helperPaint = Paint().apply {
            color = Color.parseColor("#555555")
            style = Paint.Style.STROKE
            strokeWidth = 0.8f
        }
        val dimTextPaint = Paint().apply {
            color = Color.parseColor("#555555")
            textSize = 9f
            textAlign = Paint.Align.CENTER
        }
        val cutCirclePaint = Paint().apply {
            color = Color.parseColor("#c0392b")
            style = Paint.Style.FILL
        }
        val cutTextPaint = Paint().apply {
            color = Color.WHITE
            textSize = 8f
            textAlign = Paint.Align.CENTER
            isFakeBoldText = true
        }

        val scaledCuts = layout.cuts.map {
            CutLineData(
                number = it.number,
                orientation = it.orientation,
                position = if (it.orientation == "H") oy + it.position * s else ox + it.position * s,
            )
        }
        val horizontalCuts = scaledCuts.filter { it.orientation == "H" }
        val verticalCuts = scaledCuts.filter { it.orientation == "V" }
        val hDimMarkers = placeHorizontalMarkers(
            horizontalCuts,
            anchorX = ox,
            labelX = ox - 22f,
            minSep = 18f,
        )
        val vDimMarkers = placeVerticalMarkers(
            verticalCuts,
            anchorY = oy,
            labelY = oy - 18f,
            minSep = 20f,
        )
        val hCutMarkers = placeHorizontalMarkers(
            horizontalCuts,
            anchorX = ox + layout.sheetW * s,
            labelX = ox + layout.sheetW * s + 22f,
            minSep = 20f,
        )
        val vCutMarkers = placeVerticalMarkers(
            verticalCuts,
            anchorY = oy + layout.sheetH * s,
            labelY = oy + layout.sheetH * s + 26f,
            minSep = 24f,
        )

        for (cut in horizontalCuts) {
            c.drawLine(ox, cut.position, ox + layout.sheetW * s, cut.position, cutPaint)
            c.drawLine(ox - 10f, cut.position, ox, cut.position, helperPaint)
        }
        for (cut in verticalCuts) {
            c.drawLine(cut.position, oy, cut.position, oy + layout.sheetH * s, cutPaint)
            c.drawLine(cut.position, oy, cut.position, oy - 10f, helperPaint)
        }

        val originalCutValues = layout.cuts.associateBy({ it.number }, { it.position.roundToInt() })

        for (marker in hDimMarkers) {
            c.drawLine(marker.anchorX - 10f, marker.anchorY, marker.labelX + 4f, marker.labelY, helperPaint)
            c.drawText(originalCutValues[marker.cut.number].toString(), marker.labelX, marker.labelY + 3f, dimTextPaint)
        }
        for (marker in vDimMarkers) {
            c.drawLine(marker.anchorX, marker.anchorY - 10f, marker.labelX, marker.labelY + 4f, helperPaint)
            c.drawText(originalCutValues[marker.cut.number].toString(), marker.labelX, marker.labelY - 3f, dimTextPaint)
        }

        val hCircleR = 9f
        val vCircleR = 8f
        for (marker in hCutMarkers) {
            c.drawLine(marker.anchorX, marker.anchorY, marker.labelX - hCircleR - 3f, marker.labelY, helperPaint)
            c.drawCircle(marker.labelX, marker.labelY, hCircleR, cutCirclePaint)
            drawCenteredText(c, marker.cut.number.toString(), marker.labelX, marker.labelY, cutTextPaint)
        }
        for (marker in vCutMarkers) {
            c.drawLine(marker.anchorX, marker.anchorY, marker.labelX, marker.labelY - vCircleR - 3f, helperPaint)
            c.drawCircle(marker.labelX, marker.labelY, vCircleR, cutCirclePaint)
            drawCenteredText(c, marker.cut.number.toString(), marker.labelX, marker.labelY, cutTextPaint)
        }

        doc.finishPage(page)
    }

    val fileName = "${baseName(projectName)}.pdf"
    return writeToDownloads(context, fileName, "application/pdf") { out ->
        doc.writeTo(out)
    }.also { doc.close() }
}

// ── SVG ───────────────────────────────────────────────────────────────────

fun exportSvg(context: Context, layouts: List<SheetResult>, projectName: String): String {
    val saved = mutableListOf<String>()
    val base = baseName(projectName)

    layouts.forEachIndexed { idx, layout ->
        val dim = 50f
        val ox = dim
        val oy = dim
        val sw = layout.sheetW
        val sh = layout.sheetH
        val circleR = max(7f, min(sw, sh) / 55f)
        val cuts = layout.cuts
        val hDimMarkers = placeHorizontalMarkers(
            cuts.filter { it.orientation == "H" },
            anchorX = ox,
            labelX = ox - 18f,
            minSep = 18f,
        )
        val vDimMarkers = placeVerticalMarkers(
            cuts.filter { it.orientation == "V" },
            anchorY = oy,
            labelY = oy - 18f,
            minSep = 18f,
        )
        val hCutMarkers = placeHorizontalMarkers(
            cuts.filter { it.orientation == "H" },
            anchorX = ox + sw,
            labelX = ox + sw + circleR + 18f,
            minSep = circleR * 2 + 6f,
        )
        val vCutMarkers = placeVerticalMarkers(
            cuts.filter { it.orientation == "V" },
            anchorY = oy + sh,
            labelY = oy + sh + circleR + 26f,
            minSep = circleR * 2 + 6f,
        )
        val cutValues = cuts.associateBy({ it.number }, { it.position.roundToInt() })

        val sb = StringBuilder()
        sb.appendLine("""<?xml version="1.0" encoding="UTF-8"?>""")
        sb.appendLine("""<svg xmlns="http://www.w3.org/2000/svg" width="${sw + 2 * dim}" height="${sh + 2 * dim}">""")
        sb.appendLine("""  <rect x="$ox" y="$oy" width="$sw" height="$sh" fill="#f5f5f0" stroke="#333" stroke-width="2"/>""")

        layout.placements.forEach { rect ->
            val px = ox + rect.x
            val py = oy + rect.y
            val hex = "#%06X".format(rect.color and 0xFFFFFF)
            sb.appendLine(
                """  <rect x="$px" y="$py" width="${rect.w}" height="${rect.h}" """ +
                    """fill="$hex" fill-opacity="0.7" stroke="#444" stroke-width="1"/>"""
            )
            sb.appendLine(
                """  <text x="${px + rect.w / 2}" y="${py + rect.h / 2}" font-size="10" text-anchor="middle" fill="black">""" +
                    """${rect.label.ifBlank { "${rect.w.toInt()}×${rect.h.toInt()}" }}</text>"""
            )
        }

        cuts.filter { it.orientation == "H" }.forEach { cut ->
            val cy = oy + cut.position
            sb.appendLine("""  <line x1="$ox" y1="$cy" x2="${ox + sw}" y2="$cy" stroke="#c0392b" stroke-width="1.5" stroke-dasharray="6,4"/>""")
            sb.appendLine("""  <line x1="${ox - 16}" y1="$cy" x2="$ox" y2="$cy" stroke="#444" stroke-width="1"/>""")
        }
        cuts.filter { it.orientation == "V" }.forEach { cut ->
            val cx = ox + cut.position
            sb.appendLine("""  <line x1="$cx" y1="$oy" x2="$cx" y2="${oy + sh}" stroke="#c0392b" stroke-width="1.5" stroke-dasharray="6,4"/>""")
            sb.appendLine("""  <line x1="$cx" y1="${oy - 16}" x2="$cx" y2="$oy" stroke="#444" stroke-width="1"/>""")
        }

        hDimMarkers.forEach { marker ->
            sb.appendLine("""  <line x1="${marker.anchorX - 16}" y1="${marker.anchorY}" x2="${marker.labelX + 4}" y2="${marker.labelY}" stroke="#444" stroke-width="1"/>""")
            sb.appendLine("""  <text x="${marker.labelX}" y="${marker.labelY}" font-size="8" text-anchor="end" dominant-baseline="middle" fill="#555">${cutValues[marker.cut.number]}</text>""")
        }
        vDimMarkers.forEach { marker ->
            sb.appendLine("""  <line x1="${marker.anchorX}" y1="${marker.anchorY - 16}" x2="${marker.labelX}" y2="${marker.labelY + 4}" stroke="#444" stroke-width="1"/>""")
            sb.appendLine("""  <text x="${marker.labelX}" y="${marker.labelY}" font-size="8" text-anchor="middle" dominant-baseline="middle" fill="#555">${cutValues[marker.cut.number]}</text>""")
        }

        hCutMarkers.forEach { marker ->
            sb.appendLine("""  <line x1="${marker.anchorX}" y1="${marker.anchorY}" x2="${marker.labelX - circleR - 2}" y2="${marker.labelY}" stroke="#c0392b" stroke-width="1"/>""")
            sb.appendLine("""  <circle cx="${marker.labelX}" cy="${marker.labelY}" r="$circleR" fill="#c0392b"/>""")
            sb.appendLine("""  <text x="${marker.labelX}" y="${marker.labelY}" font-size="${max(6f, circleR - 2f)}" text-anchor="middle" dominant-baseline="middle" fill="white">${marker.cut.number}</text>""")
        }
        vCutMarkers.forEach { marker ->
            sb.appendLine("""  <line x1="${marker.anchorX}" y1="${marker.anchorY}" x2="${marker.labelX}" y2="${marker.labelY - circleR - 2}" stroke="#c0392b" stroke-width="1"/>""")
            sb.appendLine("""  <circle cx="${marker.labelX}" cy="${marker.labelY}" r="$circleR" fill="#c0392b"/>""")
            sb.appendLine("""  <text x="${marker.labelX}" y="${marker.labelY}" font-size="${max(6f, circleR - 2f)}" text-anchor="middle" dominant-baseline="middle" fill="white">${marker.cut.number}</text>""")
        }

        sb.appendLine("</svg>")

        val fileName = "${base}_sheet_${(idx + 1).toString().padStart(2, '0')}.svg"
        saved += writeToDownloads(context, fileName, "image/svg+xml") { out ->
            out.write(sb.toString().toByteArray())
        }
    }

    return if (saved.isEmpty()) "No SVG exported." else "Saved ${saved.size} SVG file(s) to Downloads."
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
