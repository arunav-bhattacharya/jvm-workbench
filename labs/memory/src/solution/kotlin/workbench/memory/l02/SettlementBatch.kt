package workbench.memory.l02

class SettlementBatch(private val merchantCount: Int) {

    fun totalsByMerchant(merchantIds: IntArray, amountsMinor: LongArray): LongArray {
        val totals = LongArray(merchantCount)        // the only allocation: one primitive slot per merchant
        for (i in merchantIds.indices) {             // compiles to a plain index loop, no iterator
            totals[merchantIds[i]] += amountsMinor[i]
        }
        return totals
    }

    fun rollingSums(amountsMinor: LongArray, window: Int): LongArray {
        require(window in 1..amountsMinor.size) { "window must be between 1 and ${amountsMinor.size}" }
        val result = LongArray(amountsMinor.size - window + 1)
        var sum = 0L
        for (i in 0 until window) sum += amountsMinor[i]          // the first window
        result[0] = sum
        for (i in window until amountsMinor.size) {
            sum += amountsMinor[i] - amountsMinor[i - window]      // slide: add the new amount, drop the oldest
            result[i - window + 1] = sum
        }
        return result
    }
}
