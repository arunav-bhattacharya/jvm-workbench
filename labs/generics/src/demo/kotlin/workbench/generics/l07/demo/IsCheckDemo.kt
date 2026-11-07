package workbench.generics.l07.demo

/** A webhook payload arrives as Any? from a JSON library. Find out what it is. */
fun shape(payload: Any?): String = when (payload) {
    null -> "empty"
    is Map<*, *> -> "object with keys ${payload.keys}"        // smart cast to Map<*, *>
    is List<*> -> "array of ${payload.size}"                  // smart cast to List<*>
    else -> "value $payload"
}

/** Safe: check every element instead of trusting the list's type. */
fun amountsIn(payload: Any?): List<Long> {
    if (payload !is List<*>) return emptyList()
    return payload.mapNotNull { it as? Long }                 // as? gives null for non-Longs
}

fun main() {
    val webhook: Any? = mapOf("id" to "pay_1", "amounts" to listOf(1_200L, "oops", 350L))
    println(shape(webhook))
    println(shape(listOf(1, 2, 3)))
    println(shape(42))

    val amounts = (webhook as Map<*, *>)["amounts"]
    println("amounts = ${amountsIn(amounts)}")

    // Wrong move. Uncomment, predict the error, then run.
    // if (amounts is List<Long>) println("a list of longs")
}
