package workbench.patterns.l07

// The same delivery prices as a map of strategies and as a when. Add a way to deliver and watch which one tells you.

enum class Way { BIKE, VAN, PICKUP }
data class Job(val way: Way, val grams: Int)

// open set: one function per way, in a map that settings or plug-ins could fill
private val strategies: Map<Way, (Job) -> Long> = mapOf(
    Way.BIKE to { j -> 200L + j.grams * 30 / 1_000 },
    Way.VAN to { _ -> 450L },
    Way.PICKUP to { _ -> 0L },
)

// closed set: one when, checked by the compiler
private fun priceWhen(j: Job): Long = when (j.way) {
    Way.BIKE -> 200L + j.grams * 30 / 1_000
    Way.VAN -> 450
    Way.PICKUP -> 0
}

fun main() {
    for (w in Way.entries) {
        val j = Job(w, 2_500)
        print("%-7s when=%d".format(w, priceWhen(j)))
        println("  map=%d".format(strategies.getValue(w)(j)))
    }
}
