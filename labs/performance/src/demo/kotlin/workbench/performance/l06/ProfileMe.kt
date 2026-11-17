package workbench.performance.l06

import kotlin.concurrent.thread

// Kotlin twin of ProfileMe.java (with SlowReport in Kotlin): four threads run kReadingSeconds for 8 seconds.
// While it runs, attach from another terminal:  asprof -d 5 -f cpu.html <pid>

data class KDocument(val id: String, val language: String, val text: String)

@Volatile var kDebugEnabled = false                     // DEBUG logging is off, as it usually is

fun kDebug(message: String) { if (kDebugEnabled) println(message) }

fun kReadingSeconds(d: KDocument): Long {
    require(Regex("^[a-z]{2}$").matches(d.language)) { "bad language" }   // a regex compiled per call
    val words = d.text.split(' ').size.toLong()                          // a new String for every word
    val seconds = (words * 60 + 237) / 238                               // 238 words a minute, rounded up
    kDebug("document %s language=%s words=%d seconds=%d"                 // formatted, then thrown away
        .format(d.id, d.language, words, seconds))
    return seconds
}

private val kWords = "the rain came early and the river rose over the old stone bridge before noon".split(' ')
private val kLanguages = listOf("en", "fr", "de", "es", "it", "nl")

fun kDocuments(n: Int) = Array(n) { i ->
    val text = (0 until 8 + i % 7).joinToString(" ") { w -> kWords[(i * 7 + w * 3) % kWords.size] }   // 8 to 14 words
    KDocument("doc-$i", kLanguages[i % kLanguages.size], text)
}

fun kHammer(threads: Int, untilNanos: Long) {
    val ds = kDocuments(4_096)
    (0 until threads).map { seed ->
        thread(name = "report-$seed") {
            var sink = 0L
            var i = seed
            while (System.nanoTime() < untilNanos) sink += kReadingSeconds(ds[i++ and 4095])
            if (sink == 42L) println()
        }
    }.forEach { it.join() }
}

fun main(args: Array<String>) {
    val seconds = args.firstOrNull()?.toInt() ?: 8
    val pid = ProcessHandle.current().pid()
    println("pid $pid, running for $seconds s")
    println("attach with: asprof -d 5 -f cpu.html $pid")
    kHammer(4, System.nanoTime() + seconds * 1_000_000_000L)
    println("done")
}
