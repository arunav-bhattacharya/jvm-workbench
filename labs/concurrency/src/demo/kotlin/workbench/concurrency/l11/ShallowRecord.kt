package workbench.concurrency.l11

// A data class's vals can't be reassigned. The objects they point to can still change.
private data class LooseQuote(val pair: String, val tiers: List<String>, val signature: ByteArray)

private class SealedQuote(val pair: String, tiers: List<String>, signature: ByteArray) {
    val tiers: List<String> = java.util.List.copyOf(tiers)    // copy in: unmodifiable even through a cast
    private val sig = signature.copyOf()
    val signature: ByteArray get() = sig.copyOf()             // copy out
}

fun main() {
    val tiers = mutableListOf("up to 10k at 1.0842")
    val sig = byteArrayOf(7, 7, 7)
    val loose = LooseQuote("EURUSD", tiers, sig)              // List<String> is read-only, not immutable
    val sealed = SealedQuote("EURUSD", tiers, sig)
    val view = java.util.Collections.unmodifiableList(tiers)  // a read-only VIEW, not a copy

    tiers.add("above 10k at 9.9999")                          // the caller keeps changing its list...
    sig[0] = 0                                                // ...and its array
    loose.signature[1] = 0                                    // a reader scribbles on what it was given
    sealed.signature[1] = 0

    println("shallow: ${loose.tiers}  signature ${loose.signature.contentToString()}")
    println("deep:    ${sealed.tiers}  signature ${sealed.signature.contentToString()}")
    println("unmodifiableList view: $view")
    (loose.tiers as MutableList<String>).add("added through a cast")   // read-only interface, mutable object
    println("shallow after a cast:  ${loose.tiers}")
}
