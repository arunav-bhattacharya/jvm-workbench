package workbench.generics.l02.demo

import java.time.LocalDate

/** The bound T : Comparable<T> means "T can be compared with another T", so > is allowed. */
fun <T : Comparable<T>> maxOf2(a: T, b: T): T = if (a > b) a else b

data class Payment(val id: String, val cents: Long)

fun main() {
    println(maxOf2(1_200, 99))
    println(maxOf2("EUR", "USD"))
    println(maxOf2(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 10, 30)))

    // Wrong moves. Uncomment ONE at a time, predict the error, then run.
    // println(maxOf2(1, "a"))
    // println(maxOf2(Payment("pay_1", 500), Payment("pay_2", 900)))
}
