package workbench.functional.l08.demo

import java.time.Clock
import java.time.Duration
import java.time.Instant
import java.time.ZoneOffset

data class Leftover(val id: String, val dish: String, val cookedAt: Instant)

sealed interface FridgeDecision {
    data class ThrowOut(val id: String) : FridgeDecision
    data class Keep(val id: String, val goodFor: Duration) : FridgeDecision
}

val KEEPS_FOR: Duration = Duration.ofDays(3)

/** The core: leftovers older than three days go. Pure: the time is a parameter. */
fun decideFridge(leftovers: List<Leftover>, now: Instant): List<FridgeDecision> = leftovers.map { l ->
    val age = Duration.between(l.cookedAt, now)
    if (age >= KEEPS_FOR) FridgeDecision.ThrowOut(l.id) else FridgeDecision.Keep(l.id, KEEPS_FOR - age)
}

/** The shell: reads, calls the core, carries out the decisions. No rules in here. */
class FridgeJob(private val load: () -> List<Leftover>, private val remind: (String) -> Unit, private val clock: Clock) {
    fun run() {
        val decisions = decideFridge(load(), clock.instant())          // read, then decide
        decisions.filterIsInstance<FridgeDecision.ThrowOut>().forEach { remind(it.id) }   // act
    }
}

fun main() {
    val now = Instant.parse("2026-03-10T09:00:00Z")
    val leftovers = listOf(
        Leftover("l1", "soup", Instant.parse("2026-03-06T09:00:00Z")),   // cooked 4 days before now
        Leftover("l2", "rice", Instant.parse("2026-03-09T03:00:00Z")),   // cooked 30 hours before now
    )
    println("core, called with plain values:")
    decideFridge(leftovers, now).forEach { println("  $it") }

    println("shell, with a fixed clock and a fake phone:")
    FridgeJob({ leftovers }, { println("  reminder: throw out leftover $it") }, Clock.fixed(now, ZoneOffset.UTC)).run()
}
