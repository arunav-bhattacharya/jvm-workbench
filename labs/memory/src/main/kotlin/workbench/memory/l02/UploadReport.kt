package workbench.memory.l02

/**
 * The thumbnail service's end-of-day report on a batch of uploads. Users are numbered 0 until [userCount],
 * and every upload has a size in bytes.
 *
 * Both methods give the right answer and both allocate far too much: a boxed object for nearly every
 * upload. Rewrite them so that the only object each call allocates is the LongArray it returns.
 */
class UploadReport(private val userCount: Int) {

    /** `result[u]` is the sum of `sizes[i]` over every upload `i` with `userIds[i] == u`. */
    fun bytesByUser(userIds: IntArray, sizes: LongArray): LongArray {
        val totals = HashMap<Int, Long>()
        for (i in userIds.indices) {
            totals.merge(userIds[i], sizes[i]) { a, b -> a + b }   // boxes the key, the size and the sum
        }
        return LongArray(userCount) { totals[it] ?: 0L }
    }

    /**
     * Sum of each run of [window] consecutive upload sizes, used to spot bursts of uploads:
     * `result[i] = sizes[i] + ... + sizes[i + window - 1]`, so the result has
     * `sizes.size - window + 1` elements.
     */
    fun rollingSums(sizes: LongArray, window: Int): LongArray {
        require(window in 1..sizes.size) { "window must be between 1 and ${sizes.size}" }
        return sizes.toList()                       // boxes every size into a List<Long>
            .windowed(window) { it.sum() }          // walks each window and boxes each sum
            .toLongArray()
    }
}
