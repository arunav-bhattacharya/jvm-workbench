package workbench.kotlin.l06.demo

import workbench.kotlin.OpenForProxies
import java.lang.reflect.Modifier

/** Marked for all-open: the plugin makes the class and its members open at compile time. */
@OpenForProxies
class SettlementService {
    val feeBps: Int = 125

    fun settle(batch: String): String = "settled $batch at $feeBps bps"

    private fun secret(): Int = 42                    // private stays private, and final
}

/** Not marked: final, like every Kotlin class by default. */
class PlainHelper {
    fun help(): String = "help"
}

/** What a framework generates at build or run time: a subclass that wraps every call. */
class TimedSettlementService : SettlementService() {
    override fun settle(batch: String): String {
        val start = System.nanoTime()
        try {
            return super.settle(batch)
        } finally {
            println("  settle took ${(System.nanoTime() - start) / 1_000} us")
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
    describe(SettlementService::class.java)
    describe(PlainHelper::class.java)
    val service: SettlementService = TimedSettlementService()
    println(service.settle("batch-17"))

    // Wrong move. Delete @OpenForProxies above SettlementService, predict, run.
}
