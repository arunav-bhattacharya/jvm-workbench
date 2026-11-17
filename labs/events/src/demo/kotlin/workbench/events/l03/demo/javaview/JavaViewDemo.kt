package workbench.events.l03.demo.javaview

/** Kotlin calling the same API in JavaViewApi.kt: every call reads naturally, no door needed. */
fun main() {
    val plain = PlainBus()
    val friendly = FriendlyBus("deliveries")
    Registry.subscribe<ParcelCollected> { println("kotlin handler: ${it.parcelId} ${it.weight.grams}") }
    Registry.subscribe(ParcelCollected::class) { println("via KClass:     $it") }
    Registry.publish(ParcelCollected(ParcelId("PP-7781"), Weight(2_500)))
    println("${plain.name}, ${friendly.name}")

    try {
        ParcelId("7781")
    } catch (e: IllegalArgumentException) {
        println("refused from Kotlin: ${e.message}")
    }

    // The calls Java can't make are ordinary Kotlin:
    println(PlainBus("deliveries").name)
    println(Registry.describe(ParcelId("PP-7781")))
}
