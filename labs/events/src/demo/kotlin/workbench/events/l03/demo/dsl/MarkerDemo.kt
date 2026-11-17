package workbench.events.l03.demo.dsl

// Uses the DSL in DslDemo.kt. EventsDsl there is annotated with @DslMarker.

fun main() {
    val bus = Bus()
    val timings = Timings()
    bus.subscriptions(timings) {
        timed("load") {
            on<ParcelCollected> { println("load     +${it.grams} g") }

            // Step 2: uncomment. You meant "time deliveries inside the load group". Run it.
            // timed("deliveries") { on<ParcelDelivered> { println("load     -${it.grams} g") } }

            // Step 4: uncomment instead. The label says which builder you mean.
            // this@subscriptions.timed("deliveries") { on<ParcelDelivered> { println("load     -${it.grams} g") } }
        }
    }
    bus.publish(ParcelCollected("PP-7781", 2_500))
    bus.publish(ParcelDelivered("PP-7781", 2_500))
    println("timed groups: ${timings.calls}")
}
