package workbench.bytecode.l05

/** Receives one record per intercepted call, e.g. `"FxQuoteService.quote", 5_000_000, false`. */
fun interface TimingSink {
    fun record(method: String, nanos: Long, failed: Boolean)
}
