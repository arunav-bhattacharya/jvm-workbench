package workbench.events.l03.demo.dsl

// Uses the DSL in DslDemo.kt. EventsDsl there is annotated with @DslMarker.

fun main() {
    val bus = Bus()
    val timings = Timings()
    bus.subscriptions(timings) {
        timed("ledger") {
            on<PaymentCaptured> { println("ledger  +${it.cents}") }

            // Step 2: uncomment. You meant "time refunds inside the ledger group". Run it.
            // timed("refunds") { on<PaymentRefunded> { println("ledger  -${it.cents}") } }

            // Step 4: uncomment instead. The label says which builder you mean.
            // this@subscriptions.timed("refunds") { on<PaymentRefunded> { println("ledger  -${it.cents}") } }
        }
    }
    bus.publish(PaymentCaptured("pay_7781", 1_999))
    bus.publish(PaymentRefunded("pay_7781", 500))
    println("timed groups: ${timings.calls}")
}
