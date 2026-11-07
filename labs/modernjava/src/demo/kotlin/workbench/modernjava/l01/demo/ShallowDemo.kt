package workbench.modernjava.l01.demo

// List<String> is a read-only view in Kotlin, not an immutable list: the caller may still hold a MutableList
data class Batch(val id: String, val paymentIds: List<String>)

// Kotlin can't reassign a constructor parameter, so the defensive copy goes in a factory
data class SafeBatch(val id: String, val paymentIds: List<String>) {
    companion object {
        fun of(id: String, paymentIds: List<String>) = SafeBatch(id, java.util.List.copyOf(paymentIds))
    }
}

data class Rate(val value: Double)

/** Equality, hashCode and toString are only as deep as the properties. */
fun main() {
    val ids = mutableListOf("pay_1", "pay_2")
    val batch = Batch("b-7", ids)
    val sent = hashSetOf(batch)
    val before = batch.hashCode()

    ids += "pay_3"                                              // someone reuses their list

    println("batch now:          $batch")
    println("hashCode changed:   ${before != batch.hashCode()}")
    println("sent.contains:      ${batch in sent}")

    val copy = batch.copy(id = "b-9")                           // copy() is shallow too
    ids += "pay_4"
    println("copy shares list:   $copy")

    val ids2 = mutableListOf("pay_1", "pay_2")
    val safe = SafeBatch.of("b-8", ids2)
    ids2 += "pay_3"
    println("safe batch:         $safe")

    println("NaN data class ==:  ${Rate(Double.NaN) == Rate(Double.NaN)}  (but NaN == NaN is ${Double.NaN == Double.NaN})")
    println("0.0 vs -0.0 ==:     ${Rate(0.0) == Rate(-0.0)} (but 0.0 == -0.0 is ${0.0 == -0.0})")
}
