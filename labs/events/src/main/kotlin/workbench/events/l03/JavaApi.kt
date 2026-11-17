package workbench.events.l03

import java.util.function.Consumer

/**
 * The door for Java callers. The model's constructors take value classes, so Java can't call them
 * (they are private plus a synthetic overload), and its getters have mangled names. This facade
 * takes and returns plain String and long, and still validates: it builds the value classes, so
 * every init block runs.
 *
 * @JvmStatic makes each function a real static method: Java writes Events.collected(...), not
 * Events.INSTANCE.collected(...).
 */
object Events {
    @JvmStatic
    fun booked(parcelId: String, grams: Long): ParcelBooked =
        ParcelBooked(ParcelId(parcelId), Weight(grams))

    /** TODO 6: like booked above. */
    @JvmStatic
    fun collected(parcelId: String, grams: Long): ParcelCollected = TODO("build a ParcelCollected")

    @JvmStatic
    fun delivered(parcelId: String, grams: Long): ParcelDelivered =
        ParcelDelivered(ParcelId(parcelId), Weight(grams))

    @JvmStatic
    fun failed(parcelId: String, reason: FailReason): DeliveryFailed =
        DeliveryFailed(ParcelId(parcelId), reason)

    /** TODO 6: the id as a plain String. */
    @JvmStatic
    fun parcelId(event: ParcelEvent): String = TODO("unwrap the ParcelId")

    /** TODO 6: the weight in grams. */
    @JvmStatic
    fun grams(event: Handover): Long = TODO("unwrap the Weight")

    @JvmStatic
    fun grams(event: ParcelBooked): Long = event.weight.grams

    /**
     * The subscription DSL for Java: Events.subscriptions(bus, b -> { b.on(ParcelCollected.class, e -> ...); }).
     * A Consumer, not a Function1, so the Java lambda needs no `return Unit.INSTANCE`.
     *
     * TODO 6: call SubscriptionsBuilder.build with a receiver lambda that hands `this` to block.accept.
     */
    @JvmStatic
    @JvmOverloads
    fun subscriptions(bus: EventBus, timings: Timings = Timings(), block: Consumer<SubscriptionsBuilder>): Subscription =
        TODO("SubscriptionsBuilder.build(bus, timings) { ... }")
}
