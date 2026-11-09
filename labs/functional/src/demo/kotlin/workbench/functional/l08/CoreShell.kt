package workbench.functional.l08

import java.time.Clock
import java.time.Duration
import java.time.Instant
import java.time.ZoneOffset

data class PendingAuth(val id: String, val amountMinor: Long, val authorizedAt: Instant)

sealed interface VoidDecision {
    data class VoidIt(val authId: String) : VoidDecision
    data class Keep(val authId: String, val expiresIn: Duration) : VoidDecision
}

val AUTH_LIFETIME: Duration = Duration.ofDays(7)

/** The core: authorizations older than seven days are voided. Pure: the time is a parameter. */
fun decideVoids(auths: List<PendingAuth>, now: Instant): List<VoidDecision> = auths.map { a ->
    val age = Duration.between(a.authorizedAt, now)
    if (age >= AUTH_LIFETIME) VoidDecision.VoidIt(a.id) else VoidDecision.Keep(a.id, AUTH_LIFETIME - age)
}

/** The shell: reads, calls the core, carries out the decisions. No rules in here. */
class VoidJob(private val load: () -> List<PendingAuth>, private val voidAuth: (String) -> Unit, private val clock: Clock) {
    fun run() {
        val decisions = decideVoids(load(), clock.instant())          // read, then decide
        decisions.filterIsInstance<VoidDecision.VoidIt>().forEach { voidAuth(it.authId) }   // act
    }
}

fun main() {
    val now = Instant.parse("2026-03-10T09:00:00Z")
    val auths = listOf(
        PendingAuth("a1", 1_999, now.minus(Duration.ofDays(8))),
        PendingAuth("a2", 4_250, now.minus(Duration.ofHours(30))),
    )
    println("core, called with plain values:")
    decideVoids(auths, now).forEach { println("  $it") }

    println("shell, with a fixed clock and a fake gateway:")
    VoidJob({ auths }, { println("  POST /authorizations/$it/void") }, Clock.fixed(now, ZoneOffset.UTC)).run()
}
