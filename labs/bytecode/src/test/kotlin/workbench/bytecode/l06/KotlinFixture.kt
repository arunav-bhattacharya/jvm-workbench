package workbench.bytecode.l06

/** A Kotlin class for the reader: a data class, a companion constant and a default argument. */
data class KotlinFixture(val scene: String, val runMillis: Long = 9_000_000_000L) {
    fun line(dimmer: Double = 0.8642) = "$scene ${runMillis * dimmer}"

    companion object {
        const val MAX_MILLIS = 10_000_000L
    }
}
