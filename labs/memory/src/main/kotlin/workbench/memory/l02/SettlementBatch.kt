package workbench.memory.l02

/**
 * End-of-day settlement for a batch of payments. Merchants are numbered 0 until [merchantCount].
 *
 * Both methods give the right answer and both allocate far too much: a boxed object for nearly every
 * payment. Rewrite them so that the only object each call allocates is the LongArray it returns.
 */
class SettlementBatch(private val merchantCount: Int) {

    /** `result[m]` is the sum of `amountsMinor[i]` over every payment `i` with `merchantIds[i] == m`. */
    fun totalsByMerchant(merchantIds: IntArray, amountsMinor: LongArray): LongArray {
        val totals = HashMap<Int, Long>()
        for (i in merchantIds.indices) {
            totals.merge(merchantIds[i], amountsMinor[i]) { a, b -> a + b }   // boxes the key, the amount and the sum
        }
        return LongArray(merchantCount) { totals[it] ?: 0L }
    }

    /**
     * Sum of each run of [window] consecutive amounts, used to spot bursts on a card:
     * `result[i] = amountsMinor[i] + ... + amountsMinor[i + window - 1]`, so the result has
     * `amountsMinor.size - window + 1` elements.
     */
    fun rollingSums(amountsMinor: LongArray, window: Int): LongArray {
        require(window in 1..amountsMinor.size) { "window must be between 1 and ${amountsMinor.size}" }
        return amountsMinor.toList()                // boxes every amount into a List<Long>
            .windowed(window) { it.sum() }          // walks each window and boxes each sum
            .toLongArray()
    }
}
