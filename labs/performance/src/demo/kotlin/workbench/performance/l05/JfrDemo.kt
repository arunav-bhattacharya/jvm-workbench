package workbench.performance.l05

import jdk.jfr.Category
import jdk.jfr.Description
import jdk.jfr.Event
import jdk.jfr.Label
import jdk.jfr.Name
import java.nio.file.Path
import java.util.concurrent.ThreadLocalRandom
import kotlin.concurrent.thread

// Kotlin twin of JfrDemo.java (with its workload and event in this one file). It runs the workload
// for 4 seconds in a second JVM started with -XX:StartFlightRecording and writes build/perf05-kt.jfr.

@Name("workbench.StoreCall")
@Label("Store Call")
@Category("Workbench", "Reports")
@Description("A call to the document store while writing a report")
class KStoreCallEvent : Event() {
    @Label("Shelf") var shelf: String? = null               // a Kotlin property: JFR records its field
    @Label("Words") var words = 0L
    @Label("Found") var found = false
}

private val archive = Any()

fun kCountWords(line: String): Long = line.split(' ').size.toLong()   // allocates: a new String for every word

fun kCallStore(shelf: String, doc: Int): Long {
    val event = KStoreCallEvent()
    event.begin()
    Thread.sleep(ThreadLocalRandom.current().nextInt(2, if (shelf == "shelf-7") 40 else 12).toLong())
    val found = doc % 17 != 0
    val words = if (found) 200L + doc % 3_000 else 0L
    event.end()
    if (event.shouldCommit()) {                            // skip the field work when no recording wants it
        event.shelf = shelf
        event.words = words
        event.found = found
        event.commit()
    }
    return words
}

fun kRunWorkload(seconds: Int) {
    val until = System.nanoTime() + seconds * 1_000_000_000L
    val workers = (0 until 4).map { w ->
        thread(name = "report-$w") {
            var sink = 0L
            var i = 0
            while (System.nanoTime() < until) {
                for (k in 0 until 2_000) sink += kCountWords("page ${(k + i) % 9_000} of the weekly report on rain")
                sink += kCallStore("shelf-${i % 10}", i)
                if (i % 10 == w) synchronized(archive) { Thread.sleep(15) }   // writing to the shared archive
                i++
            }
            if (sink == 42L) println()
        }
    }
    workers.forEach { it.join() }
}

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") return kRunWorkload(4)
    val file = Path.of("build", "perf05-kt.jfr").toAbsolutePath()
    val java = ProcessHandle.current().info().command().orElse("java")
    ProcessBuilder(java, "-XX:StartFlightRecording:filename=$file,settings=profile",
        "-cp", System.getProperty("java.class.path"), "workbench.performance.l05.JfrDemoKt", "child")
        .inheritIO().start().waitFor()
    println("recording written to $file")
    println("try: jfr summary $file")
}
