package workbench.generics.l10

/**
 * A fluent builder hierarchy for the shop's order forms. The common setters live in the base class,
 * and each one must return the SUBCLASS type, so that `GiftBoxBuilder().grams(1_200).ribbon("red")`
 * keeps going.
 *
 * The recursive bound `B : OrderBuilder<B>` is how the base class names "my own subclass".
 * Each subclass passes itself: `class GiftBoxBuilder : OrderBuilder<GiftBoxBuilder>()`.
 * The signatures are done. Write the bodies.
 */
abstract class OrderBuilder<B : OrderBuilder<B>> {
    protected var grams: Int = 0
    protected var variety: String? = null
    protected var note: String = ""

    /** Sets the weight in grams and returns this builder, typed as the subclass. */
    fun grams(grams: Int): B = TODO("store it, then return self()")

    /** Sets the variety, such as "Gala". */
    fun variety(name: String): B = TODO("store it, then return self()")

    /** Sets the note for the order. Optional: it defaults to "". */
    fun note(text: String): B = TODO("store it, then return self()")

    /** `this`, typed as the subclass. Each subclass implements it as `= this`. */
    protected abstract fun self(): B

    /**
     * Checks the common fields before a subclass builds:
     * throws IllegalStateException("weight must be positive") if grams <= 0,
     * and IllegalStateException("variety is required") if no variety was set.
     */
    protected fun checkCommon() {
        TODO("use check(...) twice")
    }
}

class GiftBoxBuilder : OrderBuilder<GiftBoxBuilder>() {
    private var ribbon: String? = null

    fun ribbon(colour: String): GiftBoxBuilder = TODO("store it, return this")

    override fun self(): GiftBoxBuilder = TODO("return this")

    /** Checks the common fields, then IllegalStateException("ribbon is required"), then builds. */
    fun build(): GiftBox = TODO("checkCommon(), check the ribbon, build the GiftBox")
}

class DeliveryBuilder : OrderBuilder<DeliveryBuilder>() {
    private var address: String? = null

    fun address(text: String): DeliveryBuilder = TODO("store it, return this")

    override fun self(): DeliveryBuilder = TODO("return this")

    /** Checks the common fields, then IllegalStateException("address is required"), then builds. */
    fun build(): Delivery = TODO("checkCommon(), check the address, build the Delivery")
}
