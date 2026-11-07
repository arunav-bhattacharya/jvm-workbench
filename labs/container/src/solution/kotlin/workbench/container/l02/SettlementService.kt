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

/** Settles a batch of card payments. It has no interface, so the container intercepts it with a subclass. */
@Component
open class SettlementService(private val ledger: SettlementLedger) {     // open: a subclass may extend it
    @Timed
    open fun settle(batch: String): String {                              // open: a subclass may override it
        audit(batch)                       // a self-call: intercepted, because the subclass IS this object
        ledger.post(batch)
        return "settled $batch"
    }

    @Timed
    open fun audit(batch: String) = check(batch.startsWith("B-")) { "bad batch id $batch" }

    fun region(): String = "EU"            // not intercepted, so it may stay final
}
