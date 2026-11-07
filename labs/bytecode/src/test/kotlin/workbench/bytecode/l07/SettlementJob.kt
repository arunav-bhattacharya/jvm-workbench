package workbench.bytecode.l07

/** A final Kotlin class (no `open`): a subclass proxy couldn't touch it, an agent can. */
class SettlementJob {
    fun settle(batch: String): String {
        processed++
        return "settled $batch"
    }

    /** Calls settle on `this`: a forwarding proxy would miss these calls. */
    fun settleAll(batches: List<String>): Int {
        batches.forEach { settle(it) }
        return batches.size
    }

    fun audit(batch: String) = "audited $batch"

    companion object {
        @JvmField var processed = 0
    }
}
