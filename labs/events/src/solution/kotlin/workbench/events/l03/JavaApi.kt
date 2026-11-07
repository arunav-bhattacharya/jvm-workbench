package workbench.events.l03

import java.util.function.Consumer

/**
 * The door for Java callers. The model's constructors take value classes, so Java can't call them
 * (they are private plus a synthetic overload), and its getters have mangled names. This facade
 * takes and returns plain String and long, and still validates: it builds the value classes, so
 * every init block runs.
 *
 * @JvmStatic makes each function a real static method: Java writes Events.captured(...), not
 * Events.INSTANCE.captured(...).
 */
object Events {
    @JvmStatic
    fun authorized(paymentId: String, amountMinor: Long): PaymentAuthorized =
        PaymentAuthorized(PaymentId(paymentId), Money(amountMinor))

    @JvmStatic
    fun captured(paymentId: String, amountMinor: Long): PaymentCaptured =
        PaymentCaptured(PaymentId(paymentId), Money(amountMinor))

    @JvmStatic
    fun refunded(paymentId: String, amountMinor: Long): PaymentRefunded =
        PaymentRefunded(PaymentId(paymentId), Money(amountMinor))

    @JvmStatic
    fun declined(paymentId: String, reason: DeclineReason): PaymentDeclined =
        PaymentDeclined(PaymentId(paymentId), reason)

    @JvmStatic
    fun paymentId(event: PaymentEvent): String = event.paymentId.value

    @JvmStatic
    fun amountMinor(event: MoneyMovement): Long = event.amount.minor

    @JvmStatic
    fun amountMinor(event: PaymentAuthorized): Long = event.amount.minor

    /**
     * The subscription DSL for Java: Events.subscriptions(bus, b -> { b.on(PaymentCaptured.class, e -> ...); }).
     * A Consumer, not a Function1, so the Java lambda needs no `return Unit.INSTANCE`.
     */
    @JvmStatic
    @JvmOverloads
    fun subscriptions(bus: EventBus, timings: Timings = Timings(), block: Consumer<SubscriptionsBuilder>): Subscription =
        SubscriptionsBuilder.build(bus, timings) { block.accept(this) }
}
