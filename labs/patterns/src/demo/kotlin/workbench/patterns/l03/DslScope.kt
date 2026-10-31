package workbench.patterns.l03

// A tiny refund-batch DSL. @DslMarker stops an inner block from reaching the outer builder by accident.

@DslMarker
annotation class RefundDsl

data class Refund(val paymentId: String, val amountMinor: Long)
data class RefundBatch(val reason: String, val refunds: List<Refund>)

@RefundDsl
class RefundsBuilder {
    private val refunds = mutableListOf<Refund>()
    fun refund(paymentId: String, amountMinor: Long) { refunds += Refund(paymentId, amountMinor) }
    fun build() = refunds.toList()
}

@RefundDsl
class RefundBatchBuilder {
    var reason: String = "unspecified"
    private var refunds: List<Refund> = emptyList()
    fun refunds(block: RefundsBuilder.() -> Unit) { refunds = RefundsBuilder().apply(block).build() }
    fun build() = RefundBatch(reason, refunds)
}

fun refundBatch(block: RefundBatchBuilder.() -> Unit): RefundBatch = RefundBatchBuilder().apply(block).build()

fun main() {
    val batch = refundBatch {
        reason = "duplicate charge"
        refunds {
            refund("p-101", 1_250)
            refund("p-102", 990)
            // reason = "oops"     // step 2 of the Try it: uncomment this line
        }
    }
    println(batch)
    println("total refunded: ${batch.refunds.sumOf { it.amountMinor }}")
}
