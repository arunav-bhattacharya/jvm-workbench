package workbench.bytecode.l06

/** A Kotlin class for the reader: a data class, a companion constant and a default argument. */
data class KotlinFixture(val id: String, val amountMinor: Long = 9_000_000_000L) {
    fun line(rate: Double = 1.0842) = "$id ${amountMinor * rate}"

    companion object {
        const val MAX_MINOR = 10_000_000L
    }
}
