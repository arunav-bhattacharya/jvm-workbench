package workbench.memory.l02

class UploadReport(private val userCount: Int) {

    fun bytesByUser(userIds: IntArray, sizes: LongArray): LongArray {
        val totals = LongArray(userCount)            // the only allocation: one primitive slot per user
        for (i in userIds.indices) {                 // compiles to a plain index loop, no iterator
            totals[userIds[i]] += sizes[i]
        }
        return totals
    }

    fun rollingSums(sizes: LongArray, window: Int): LongArray {
        require(window in 1..sizes.size) { "window must be between 1 and ${sizes.size}" }
        val result = LongArray(sizes.size - window + 1)
        var sum = 0L
        for (i in 0 until window) sum += sizes[i]                 // the first window
        result[0] = sum
        for (i in window until sizes.size) {
            sum += sizes[i] - sizes[i - window]                    // slide: add the new size, drop the oldest
            result[i - window + 1] = sum
        }
        return result
    }
}
