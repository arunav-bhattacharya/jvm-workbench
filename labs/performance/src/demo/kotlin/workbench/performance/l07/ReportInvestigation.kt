package workbench.performance.l07

import jdk.jfr.Configuration
import jdk.jfr.Recording
import jdk.jfr.consumer.RecordingFile
import java.lang.management.ManagementFactory
import java.nio.file.Path
import kotlin.concurrent.thread

// Kotlin twin of ReportInvestigation.java: the same versions of the report step written in Kotlin, run on
// 4 threads for 3 seconds with an in-process JFR recording, then allocation by line in this file.
// Usage: -Pargs=slow (or hoisted, scanned, noregex).

data class KtDocument(val id: String, val language: String, val text: String)

@Volatile var ktDebugEnabled = false
fun ktDebug(message: String) { if (ktDebugEnabled) println(message) }

// before: a regex per call, a new String per word, a log line formatted and dropped
fun ktSlow(d: KtDocument): Long {
    require(Regex("^[a-z]{2}$").matches(d.language)) { "bad language" }
    val words = d.text.split(' ').size.toLong()
    val seconds = (words * 60 + 237) / 238
    ktDebug("document %s language=%s words=%d seconds=%d".format(d.id, d.language, words, seconds))
    return seconds
}

// round 1: the pattern compiled once, the log line guarded
val KT_LANGUAGE = Regex("^[a-z]{2}$")

fun ktHoisted(d: KtDocument): Long {
    require(KT_LANGUAGE.matches(d.language)) { "bad language" }
    val words = d.text.split(' ').size.toLong()
    val seconds = (words * 60 + 237) / 238
    if (ktDebugEnabled) ktDebug("document %s language=%s words=%d seconds=%d".format(d.id, d.language, words, seconds))
    return seconds
}

// round 2: count where words start instead of making each word
fun ktCountWords(text: String): Long {
    var words = 0L
    var inWord = false
    for (c in text) {
        val letter = c != ' '
        if (letter && !inWord) words++
        inWord = letter
    }
    return words
}

fun ktScanned(d: KtDocument): Long {
    require(KT_LANGUAGE.matches(d.language)) { "bad language" }
    val words = ktCountWords(d.text)
    val seconds = (words * 60 + 237) / 238
    if (ktDebugEnabled) ktDebug("document %s language=%s words=%d seconds=%d".format(d.id, d.language, words, seconds))
    return seconds
}

// round 3, if the budget asks for it: no regex for two letters
fun isLanguageCodeKt(s: String) = s.length == 2 && s.all { it in 'a'..'z' }

fun ktNoRegex(d: KtDocument): Long {
    require(isLanguageCodeKt(d.language)) { "bad language" }
    val words = ktCountWords(d.text)
    val seconds = (words * 60 + 237) / 238
    if (ktDebugEnabled) ktDebug("document %s language=%s words=%d seconds=%d".format(d.id, d.language, words, seconds))
    return seconds
}

private val ktWords = "the rain came early and the river rose over the old stone bridge before noon".split(' ')
private val ktLanguages = listOf("en", "fr", "de", "es", "it", "nl")

fun ktDocuments(n: Int) = Array(n) { i ->
    val text = (0 until 8 + i % 7).joinToString(" ") { w -> ktWords[(i * 7 + w * 3) % ktWords.size] }   // 8 to 14 words
    KtDocument("doc-$i", ktLanguages[i % ktLanguages.size], text)
}

fun main(args: Array<String>) {
    val mode = args.firstOrNull() ?: "slow"
    val step: (KtDocument) -> Long = when (mode) {
        "slow" -> ::ktSlow; "hoisted" -> ::ktHoisted; "scanned" -> ::ktScanned; else -> ::ktNoRegex
    }
    val ds = ktDocuments(4_096)
    val file = Path.of("build", "report-kt-$mode.jfr").toAbsolutePath()
    val calls = LongArray(4)
    Recording(Configuration.getConfiguration("profile")).use { rec ->
        rec.start()
        val end = System.nanoTime() + 3_000_000_000L
        (0 until 4).map { t ->
            thread {
                var sink = 0L
                var i = t
                while (System.nanoTime() < end) { sink += step(ds[i and 4095]); i++; calls[t]++ }
                if (sink == 42L) println()
            }
        }.forEach { it.join() }
        rec.stop()
        rec.dump(file)
    }
    val gcs = ManagementFactory.getGarbageCollectorMXBeans().sumOf { it.collectionCount }
    println("%s: %,d calls/s, %d GCs".format(mode, calls.sum() / 3, gcs))

    val weight = HashMap<String, Long>()
    for (e in RecordingFile.readAllEvents(file)) {
        if (e.eventType.name != "jdk.ObjectAllocationSample") continue
        val frame = e.stackTrace?.frames?.firstOrNull { it.method.type.name == "workbench.performance.l07.ReportInvestigationKt" } ?: continue
        weight.merge("${frame.method.name} line ${frame.lineNumber}", e.getLong("weight"), Long::plus)
    }
    val total = weight.values.sum()
    println("allocation by line in ReportInvestigation.kt:")
    weight.entries.sortedByDescending { it.value }.take(5)
        .forEach { (site, w) -> println("  %5.1f%%  %s".format(100.0 * w / total, site)) }
}
