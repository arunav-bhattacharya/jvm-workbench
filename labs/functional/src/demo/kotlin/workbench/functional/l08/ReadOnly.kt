package workbench.functional.l08

import java.math.BigDecimal

data class Batch(val id: String, val paymentIds: List<String>)
data class Fee(val merchantId: String, val amount: BigDecimal)
data class Tagged(val id: String, val tags: MutableList<String>)

fun main() {
    // 1. a read-only List can be a view of a list someone else still changes
    val backing = mutableListOf("p1")
    val batch = Batch("b-7", backing)
    backing += "p2"
    println("1. batch after the caller adds p2: ${batch.paymentIds}")

    // 2. read-only is a compile-time view: a cast gets around it
    (batch.paymentIds as MutableList<String>) += "p3"
    println("2. after a cast and an add:       ${batch.paymentIds}")

    // 3. listOf gives a fixed-size view of an array on the JVM
    val fixed = listOf("p1", "p2")
    println("3. listOf's class: ${fixed.javaClass.name}")
    (fixed as MutableList<String>)[0] = "p9"
    println("   after set(0, \"p9\"): $fixed")
    try {
        fixed.add("p3")
    } catch (e: UnsupportedOperationException) {
        println("   add: UnsupportedOperationException")
    }

    // 4. copy() is shallow: both copies share one list
    val a = Tagged("p1", mutableListOf("card"))
    val b = a.copy(id = "p2")
    b.tags += "refund"
    println("4. a.tags = ${a.tags}, same list: ${a.tags === b.tags}")

    // 5. BigDecimal.equals compares the scale too, and data class equals uses it
    println("5. Fee(10.00) == Fee(10.0): ${Fee("m-1", BigDecimal("10.00")) == Fee("m-1", BigDecimal("10.0"))}")
    println("   compareTo says equal: ${BigDecimal("10.00").compareTo(BigDecimal("10.0")) == 0}")
}
