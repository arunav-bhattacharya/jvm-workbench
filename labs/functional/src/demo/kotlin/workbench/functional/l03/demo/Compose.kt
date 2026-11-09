package workbench.functional.l03.demo

// The stdlib has no andThen for function types, so here it is. Remove it and the file stops compiling.
infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }

val addSchemeFee: (Long) -> Long = { it + 25 }          // +25 cents
val loyaltyDiscount: (Long) -> Long = { it * 90 / 100 } // 10 % off, rounded down
val capAtTenEuros: (Long) -> Long = { minOf(it, 1_000) }

fun main() {
    val price = addSchemeFee andThen loyaltyDiscount andThen capAtTenEuros
    val capFirst = capAtTenEuros andThen addSchemeFee andThen loyaltyDiscount
    for (fee in listOf(500L, 1_200L)) {
        println("fee $fee -> ${price(fee)}   (cap first: ${capFirst(fee)})")
    }

    // Built from a list, the way merchant configuration would build it.
    val steps = listOf(addSchemeFee, loyaltyDiscount, capAtTenEuros)
    val fromList = steps.fold({ x: Long -> x }) { acc, step -> acc andThen step }
    println("fromList(1200) = ${fromList(1_200)}")
}
