package workbench.patterns.l02

// Three Kotlin factory shapes, and a factory that returns a sealed result instead of throwing.

class Slot private constructor(val day: String, val hour: Int) {
    override fun toString() = "$day $hour:00"

    companion object {
        private val days = listOf("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")

        // 1. a named factory in the companion: Slot.parse("SAT 10")
        fun parse(raw: String): SlotResult {
            val day = raw.trim().substringBefore(" ").uppercase()
            val hour = raw.trim().substringAfter(" ").toIntOrNull() ?: -1
            return when {
                day !in days -> SlotResult.BadDay(day)
                hour !in 8..19 -> SlotResult.BadHour(hour)
                else -> SlotResult.Ok(Slot(day, hour))
            }
        }
    }
}

sealed interface SlotResult {
    data class Ok(val slot: Slot) : SlotResult
    data class BadDay(val text: String) : SlotResult
    data class BadHour(val hour: Int) : SlotResult
}

class Fee private constructor(val cents: Int) {
    override fun toString() = "Fee($cents cents)"

    companion object {
        private val standard = Fee(250)
        // 2. operator invoke: callers write Fee(250) and get the cached instance
        operator fun invoke(cents: Int): Fee = if (cents == 250) standard else Fee(cents)
    }
}

interface OrderBook { fun record(entry: String) }

// 3. a top-level function named like the interface, as kotlinx.coroutines does with Job() and CoroutineScope()
fun OrderBook(): OrderBook = object : OrderBook {
    override fun record(entry: String) = println("  order book <- $entry")
}

fun describe(r: SlotResult): String = when (r) {      // no else: the compiler checks every case is here
    is SlotResult.Ok -> "ok: ${r.slot}"
    is SlotResult.BadDay -> "no such day '${r.text}'"
    is SlotResult.BadHour -> "we deliver from 8 to 19, not at ${r.hour}"
}

fun main() {
    listOf("sat 10", "FRI 23", "MOON 9").forEach {
        println("parse(\"$it\") -> ${describe(Slot.parse(it))}")
    }
    println("Fee(250) === Fee(250)? ${Fee(250) === Fee(250)}")
    println("Fee(400) === Fee(400)? ${Fee(400) === Fee(400)}")
    OrderBook().record("o-17 booked for SAT 10:00")
}
