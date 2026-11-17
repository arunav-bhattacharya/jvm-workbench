package workbench.kotlin.l06.demo

import workbench.kotlin.OpenForProxies
import java.lang.reflect.Modifier

/** Marked for all-open: the plugin makes the class and its members open at compile time. */
@OpenForProxies
class PrintQueue {
    val traySize: Int = 500

    fun print(job: String): String = "printed $job from a tray of $traySize sheets"

    private fun secret(): Int = 42                    // private stays private, and final
}

/** Not marked: final, like every Kotlin class by default. */
class PlainHelper {
    fun help(): String = "help"
}

/** What a framework generates at build or run time: a subclass that wraps every call. */
class TimedPrintQueue : PrintQueue() {
    override fun print(job: String): String {
        val start = System.nanoTime()
        try {
            return super.print(job)
        } finally {
            println("  print took ${(System.nanoTime() - start) / 1_000} us")
        }
    }
}

fun describe(cls: Class<*>) {
    val methods = cls.declaredMethods.sortedBy { it.name }.joinToString { m ->
        val kind = when {
            Modifier.isPrivate(m.modifiers) -> "private"
            Modifier.isFinal(m.modifiers) -> "final"
            else -> "open"
        }
        "${m.name}:$kind"
    }
    println("${cls.simpleName}: ${if (Modifier.isFinal(cls.modifiers)) "final" else "open"} class; $methods")
}

fun main() {
    describe(PrintQueue::class.java)
    describe(PlainHelper::class.java)
    val queue: PrintQueue = TimedPrintQueue()
    println(queue.print("flyer.pdf"))

    // Wrong move. Delete @OpenForProxies above PrintQueue, predict, run.
}
