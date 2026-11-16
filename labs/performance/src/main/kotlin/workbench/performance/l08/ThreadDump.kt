package workbench.performance.l08

import java.nio.file.Files
import java.nio.file.Path

/**
 * One thread from a `jcmd <pid> Thread.print -l` dump.
 *
 * Given code: you don't need to change this file. The lab is in DumpReader.kt.
 */
data class DumpedThread(
    val name: String,
    /** The OS thread id. It is the PID column of `top -H`. JDK 18+ prints it in decimal, older JDKs in hex. */
    val nid: Long,
    /** RUNNABLE, BLOCKED, WAITING or TIMED_WAITING; empty for JVM-internal threads such as "GC Thread#0". */
    val state: String,
    /** CPU time this thread has used since it started, from `cpu=...ms`. */
    val cpuMs: Double,
    /** The stack, top frame first, without the leading "at ". */
    val frames: List<String>,
    /** Addresses of the locks this thread holds: monitors (`- locked <...>`) and `java.util.concurrent` locks. */
    val holds: Set<String>,
    /** The address in `- waiting to lock <...>` or `- parking to wait for <...>`, or null. */
    val waitsFor: String?,
)

/** One answer of [DumpReader.hottest]: a thread and how much CPU it used between two dumps. */
data class HotThread(val name: String, val nid: Long, val cpuMs: Double)

/** A parsed thread dump. Given code: you don't need to change it. */
class ThreadDump(val threads: List<DumpedThread>) {

    fun byName(name: String): DumpedThread? = threads.firstOrNull { it.name == name }

    fun byNid(nid: Long): DumpedThread? = threads.firstOrNull { it.nid == nid }

    /** The thread that holds the lock at [address], or null when nobody does (a condition queue, for example). */
    fun ownerOf(address: String): DumpedThread? = threads.firstOrNull { address in it.holds }

    companion object {
        private val HEADER = Regex("""^"(.*)" .*?cpu=([\d.]+)ms .*?nid=(0x[0-9a-fA-F]+|\d+)""")
        private val STATE = Regex("""^\s+java\.lang\.Thread\.State: (\w+)""")
        private val FRAME = Regex("""^\s+at (.+)$""")
        private val LOCKED = Regex("""^\s+- locked <(0x[0-9a-f]+)>""")
        private val WAITS_ON = Regex("""^\s+- waiting on <(0x[0-9a-f]+)>""")
        private val WANTS = Regex("""^\s+- (?:waiting to lock|parking to wait for)\s+<(0x[0-9a-f]+)>""")
        private val OWNABLE = Regex("""^\s+- <(0x[0-9a-f]+)>""")

        fun read(path: Path): ThreadDump = parse(Files.readString(path))

        fun parse(text: String): ThreadDump {
            val threads = mutableListOf<DumpedThread>()
            var current: Builder? = null
            for (line in text.lines()) {
                val header = HEADER.find(line)
                if (header != null) {
                    current?.let { threads += it.build() }
                    val (name, cpu, nid) = header.destructured
                    val id = if (nid.startsWith("0x")) nid.drop(2).toLong(16) else nid.toLong()
                    current = Builder(name, id, cpu.toDouble())
                    continue
                }
                // the deadlock report at the end repeats thread names and stacks: it is not one more thread
                if (line.startsWith("\"") || line.startsWith("JNI global") || line.startsWith("Found ")) {
                    current?.let { threads += it.build() }
                    current = null
                    continue
                }
                val b = current ?: continue
                STATE.find(line)?.let { b.state = it.groupValues[1] }
                FRAME.find(line)?.let { b.frames += it.groupValues[1] }
                LOCKED.find(line)?.let { b.holds += it.groupValues[1] }
                WAITS_ON.find(line)?.let { b.released += it.groupValues[1] }
                WANTS.find(line)?.let { b.waitsFor = b.waitsFor ?: it.groupValues[1] }
                OWNABLE.find(line)?.let { b.holds += it.groupValues[1] }
            }
            current?.let { threads += it.build() }
            return ThreadDump(threads)
        }
    }

    private class Builder(val name: String, val nid: Long, val cpuMs: Double) {
        var state = ""
        val frames = mutableListOf<String>()
        val holds = mutableSetOf<String>()
        // Object.wait() gives the monitor back, but the frame that entered synchronized still prints "- locked"
        val released = mutableSetOf<String>()
        var waitsFor: String? = null

        fun build() = DumpedThread(name, nid, state, cpuMs, frames.toList(), holds - released, waitsFor)
    }
}
