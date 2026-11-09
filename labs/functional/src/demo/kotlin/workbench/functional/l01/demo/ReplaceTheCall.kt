package workbench.functional.l01.demo

// Pure: the result depends only on the argument, and calling it changes nothing.
fun fee(amountCents: Long): Long = amountCents * 15 / 1000

// Impure: charging a card is the whole point of the call. This fake provider counts the calls.
object FakeProvider {
    var calls = 0
    fun charge(cardToken: String, amountCents: Long): String {
        calls++
        return "ch_$calls"
    }
}

fun main() {
    // 1. With a pure function, a call and its value are interchangeable.
    val f = fee(20_000)
    println("fee(20000) + fee(20000)    = ${fee(20_000) + fee(20_000)}")
    println("val f = fee(20000); f + f  = ${f + f}")

    // 2. The same "harmless" refactoring on an impure call changes what the program does.
    val c = FakeProvider.charge("tok_visa", 20_000)
    println("val c = charge(..); listOf(c, c)      -> ${listOf(c, c)}, provider calls: ${FakeProvider.calls}")

    FakeProvider.calls = 0
    val both = listOf(FakeProvider.charge("tok_visa", 20_000), FakeProvider.charge("tok_visa", 20_000))
    println("listOf(charge(..), charge(..))        -> $both, provider calls: ${FakeProvider.calls}")
}
