package workbench.functional.l02.demo

// The same "does this dish take too long?" check, written four ways. All four have the type (Int) -> Boolean.

// 1. A lambda.
val tooSlowLambda: (Int) -> Boolean = { minutes -> minutes > 60 }

// 2. An anonymous function. Same type, but `return` means "return from this function".
val tooSlowAnon: (Int) -> Boolean = fun(minutes: Int): Boolean {
    if (minutes < 0) return true                   // a negative time is a typo, so flag it too
    return minutes > 60
}

// 3. A reference to an ordinary function.
fun isTooSlow(minutes: Int): Boolean = minutes > 60
val tooSlowRef: (Int) -> Boolean = ::isTooSlow

// 4. A class that implements the function type.
class TooSlow(private val maxMinutes: Int) : (Int) -> Boolean {
    override fun invoke(minutes: Int): Boolean = minutes > maxMinutes
}

// A function type with a receiver: inside the lambda, `this` is the Int.
val isQuarterHour: Int.() -> Boolean = { this % 15 == 0 }

// A nullable function type: the caller may pass no callback at all.
fun check(minutes: Int, rule: (Int) -> Boolean, onHit: ((Int) -> Unit)? = null): Boolean {
    val hit = rule(minutes)
    if (hit) onHit?.invoke(minutes)
    return hit
}

fun main() {
    val rules = listOf(tooSlowLambda, tooSlowAnon, tooSlowRef, TooSlow(60))
    for (minutes in listOf(45, 90, -5)) println("$minutes -> ${rules.map { rule -> rule(minutes) }}")
    println("45.isQuarterHour() = ${45.isQuarterHour()}, 50.isQuarterHour() = ${50.isQuarterHour()}")
    check(90, tooSlowRef) { println("callback: $it minutes is too slow") }
    println("no callback given: ${check(90, tooSlowRef)}")
}
