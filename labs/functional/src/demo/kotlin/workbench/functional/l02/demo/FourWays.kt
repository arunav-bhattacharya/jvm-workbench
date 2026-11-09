package workbench.functional.l02.demo

// The same "is this amount over the limit?" check, written four ways. All four have the type (Long) -> Boolean.

// 1. A lambda.
val overLimitLambda: (Long) -> Boolean = { cents -> cents > 500_000 }

// 2. An anonymous function. Same type, but `return` means "return from this function".
val overLimitAnon: (Long) -> Boolean = fun(cents: Long): Boolean {
    if (cents < 0) return true                     // a negative amount is suspicious too
    return cents > 500_000
}

// 3. A reference to an ordinary function.
fun isOverLimit(cents: Long): Boolean = cents > 500_000
val overLimitRef: (Long) -> Boolean = ::isOverLimit

// 4. A class that implements the function type.
class OverLimit(private val limitCents: Long) : (Long) -> Boolean {
    override fun invoke(cents: Long): Boolean = cents > limitCents
}

// A function type with a receiver: inside the lambda, `this` is the Long.
val isRound: Long.() -> Boolean = { this % 100 == 0L }

// A nullable function type: the caller may pass no callback at all.
fun check(cents: Long, rule: (Long) -> Boolean, onHit: ((Long) -> Unit)? = null): Boolean {
    val hit = rule(cents)
    if (hit) onHit?.invoke(cents)
    return hit
}

fun main() {
    val rules = listOf(overLimitLambda, overLimitAnon, overLimitRef, OverLimit(500_000))
    for (cents in listOf(12_000L, 900_000L, -5L)) println("$cents -> ${rules.map { rule -> rule(cents) }}")
    println("120000.isRound() = ${120_000L.isRound()}, 120001.isRound() = ${120_001L.isRound()}")
    check(900_000, overLimitRef) { println("callback: $it is over the limit") }
    println("no callback given: ${check(900_000, overLimitRef)}")
}
