package workbench.container.l02

import java.util.concurrent.CopyOnWriteArrayList

@Component
class SettlementLedger {
    private val posted = CopyOnWriteArrayList<String>()

    fun post(batch: String) {
        posted += batch
    }

    fun posted(): List<String> = posted.toList()
}

/**
 * Settles a batch of card payments. It has no interface, so the container intercepts it with a
 * Byte Buddy subclass. Once your check() works, the container refuses this class: read the message.
 */
@Component
class SettlementService(private val ledger: SettlementLedger) {
    @Timed
    fun settle(batch: String): String {
        audit(batch)                       // a self-call
        ledger.post(batch)
        return "settled $batch"
    }

    @Timed
    fun audit(batch: String) = check(batch.startsWith("B-")) { "bad batch id $batch" }

    fun region(): String = "EU"
}
