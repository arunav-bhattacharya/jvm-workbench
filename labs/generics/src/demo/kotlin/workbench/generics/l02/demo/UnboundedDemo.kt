package workbench.generics.l02.demo

/** An unbounded T is "some type, maybe nullable". You may only use what every type has. */
fun <T> describe(x: T): String = "value=$x, hash=${x.hashCode()}"   // toString and hashCode work on Any?

// Wrong moves. Uncomment ONE at a time, predict the error, then run.
// fun <T> lengthOf(x: T) = x.length
// fun <T> bigger(a: T, b: T): T = if (a > b) a else b

fun main() {
    println(describe("EUR"))
    println(describe(978))
    println(describe(null))        // T is inferred as Nothing?, and null is allowed
}
