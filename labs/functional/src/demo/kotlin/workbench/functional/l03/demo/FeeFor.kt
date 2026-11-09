package workbench.functional.l03.demo

val RATES_BPS = mapOf("NL" to 140L, "DE" to 150L, "US" to 290L)   // basis points: 1 bp = 0.01 %

// Both arguments at once.
fun fee(country: String, amountCents: Long): Long = amountCents * RATES_BPS.getValue(country) / 10_000

// Partial application: fix the country now, get back a function of the amount.
fun feeFor(country: String): (Long) -> Long {
    val bps = RATES_BPS.getValue(country)                 // looked up once, right here
    return { amountCents -> amountCents * bps / 10_000 }
}

// Currying by hand: take one argument, return a function that takes the next one.
val curriedFee: (String) -> (Long) -> Long = { country -> { amountCents -> fee(country, amountCents) } }

fun main() {
    val dutch = feeFor("NL")
    println("feeFor(\"NL\")(100000)        = ${dutch(100_000)}")
    println("curriedFee(\"DE\")(100000)    = ${curriedFee("DE")(100_000)}")

    // Kotlin idioms that usually read better than a curried signature:
    val usFee = { amountCents: Long -> fee("US", amountCents) }       // a lambda that fixes one argument
    println("lambda that fixes US        = ${usFee(100_000)}")
    println("named arguments             = ${fee(amountCents = 100_000, country = "NL")}")

    val amounts = listOf(10_000L, 250_000L, 1_000_000L)
    println("amounts.map(dutch)          = ${amounts.map(dutch)}")
}
