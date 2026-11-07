package workbench.events.l03.demo.javaview

/** Kotlin calling the same API in JavaViewApi.kt: every call reads naturally, no door needed. */
fun main() {
    val plain = PlainBus()
    val friendly = FriendlyBus("refunds")
    Registry.subscribe<PaymentCaptured> { println("kotlin handler: ${it.paymentId} ${it.amount.minor}") }
    Registry.subscribe(PaymentCaptured::class) { println("via KClass:     $it") }
    Registry.publish(PaymentCaptured(PaymentId("pay_7781"), Money(1_999)))
    println("${plain.name}, ${friendly.name}")

    try {
        PaymentId("7781")
    } catch (e: IllegalArgumentException) {
        println("refused from Kotlin: ${e.message}")
    }

    // The calls Java can't make are ordinary Kotlin:
    println(PlainBus("refunds").name)
    println(Registry.describe(PaymentId("pay_7781")))
}
