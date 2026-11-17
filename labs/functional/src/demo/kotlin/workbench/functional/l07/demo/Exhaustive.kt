package workbench.functional.l07.demo

import java.time.LocalDate

/** The expected ways taking flour from the jar can fail. A closed set: the compiler knows every case. */
sealed interface JarFailure {
    data class InvalidAmount(val grams: Int) : JarFailure
    data object PastBestBefore : JarFailure
    data class NotEnough(val shortByGrams: Int) : JarFailure
    // Uncomment the next line and run again.
    // data object JarMissing : JarFailure
}

sealed interface TakeResult {
    data class Taken(val leftGrams: Int) : TakeResult
    data class Refused(val reason: JarFailure) : TakeResult
}

/** The signature now says it can fail, and how. Nothing is thrown for a short jar. */
fun takeFlour(grams: Int, leftGrams: Int, bestBefore: LocalDate, today: LocalDate): TakeResult = when {
    grams <= 0 -> TakeResult.Refused(JarFailure.InvalidAmount(grams))
    today.isAfter(bestBefore) -> TakeResult.Refused(JarFailure.PastBestBefore)
    grams > leftGrams -> TakeResult.Refused(JarFailure.NotEnough(grams - leftGrams))
    else -> TakeResult.Taken(leftGrams - grams)
}

/** The one place that knows what to tell the cook: an exhaustive when with no else branch. */
fun advice(failure: JarFailure): String = when (failure) {
    is JarFailure.InvalidAmount -> "check the amount"
    JarFailure.PastBestBefore -> "open a new bag"
    is JarFailure.NotEnough -> "buy more flour"
}

fun main() {
    val today = LocalDate.of(2026, 3, 10)
    val fresh = LocalDate.of(2026, 3, 31)
    val old = LocalDate.of(2026, 2, 28)
    val attempts = listOf(200 to fresh, -5 to fresh, 200 to old, 1_000 to fresh)
    for ((grams, bestBefore) in attempts) {
        val line = when (val result = takeFlour(grams, leftGrams = 700, bestBefore, today)) {
            is TakeResult.Taken -> "ok: ${result.leftGrams} g left"
            is TakeResult.Refused -> "${advice(result.reason)}: ${result.reason}"
        }
        println(line)
    }
}
