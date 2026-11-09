package workbench.functional.l06

enum class PayStatus { AUTHORIZED, CAPTURED }

data class Pay(val id: String, val amountMinor: Long, val status: PayStatus)

class MiniLedger {
    private val posted = mutableSetOf<String>()
    /** Returns a ledger entry id, or null when this payment was posted before. */
    fun post(p: Pay): String? = if (posted.add(p.id)) "LE-${p.id}" else null
}

fun settleCached(cached: Pay?, ledger: MiniLedger, fetch: () -> Pay): String? =
    cached?.let { ledger.post(it) } ?: run {
        println("    cache miss, fetching from the database")
        ledger.post(fetch())
    }

class Fx { var amount: Long = 0 }
class Form { var amount: Long = 0; val fx = Fx() }

data class Shop(val name: String, val scheduleId: String)
data class Schedule(val name: String, val rateBps: Int)

fun main() {
    val p = Pay("p1", 1_999, PayStatus.AUTHORIZED)

    println("1. ?.let { } ?: run { }")
    val ledger = MiniLedger()
    println("  first settle:  ${settleCached(p, ledger) { p }}")
    println("  second settle: ${settleCached(p, ledger) { p }}")

    println("2. also and apply drop the block's result")
    val captured = p.also { it.copy(status = PayStatus.CAPTURED) }
    println("  status after also { copy }: ${captured.status}")
    val total = listOf(p, p).apply { sumOf { it.amountMinor } }
    println("  total from apply { sumOf }: $total")

    println("3. nested apply")
    val form = Form().apply { fx.apply { amount = 500 } }
    println("  form.amount = ${form.amount}, form.fx.amount = ${form.fx.amount}")

    println("4. nested it")
    val shops = mapOf("m-1" to Shop("Acme Books", "eu-std"))
    val schedules = mapOf("eu-std" to Schedule("standard-eu", 290))
    val label = shops["m-1"]?.let { schedules[it.scheduleId]?.let { "${it.name}: ${it.rateBps} bps" } }
    println("  label: $label")
}
