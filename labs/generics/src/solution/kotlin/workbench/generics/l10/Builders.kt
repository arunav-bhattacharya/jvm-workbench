package workbench.generics.l10

abstract class OrderBuilder<B : OrderBuilder<B>> {
    protected var grams: Int = 0
    protected var variety: String? = null
    protected var note: String = ""

    // each setter returns self(): typed B, so the chain keeps the subclass type
    fun grams(grams: Int): B { this.grams = grams; return self() }
    fun variety(name: String): B { variety = name; return self() }
    fun note(text: String): B { note = text; return self() }

    protected abstract fun self(): B

    protected fun checkCommon() {
        check(grams > 0) { "weight must be positive" }
        check(variety != null) { "variety is required" }
    }
}

class GiftBoxBuilder : OrderBuilder<GiftBoxBuilder>() {
    private var ribbon: String? = null

    fun ribbon(colour: String): GiftBoxBuilder { ribbon = colour; return this }

    override fun self(): GiftBoxBuilder = this      // no cast needed: B is GiftBoxBuilder here

    fun build(): GiftBox {
        checkCommon()
        val r = checkNotNull(ribbon) { "ribbon is required" }
        return GiftBox(grams, variety!!, note, r)
    }
}

class DeliveryBuilder : OrderBuilder<DeliveryBuilder>() {
    private var address: String? = null

    fun address(text: String): DeliveryBuilder { address = text; return this }

    override fun self(): DeliveryBuilder = this

    fun build(): Delivery {
        checkCommon()
        val a = checkNotNull(address) { "address is required" }
        return Delivery(grams, variety!!, note, a)
    }
}
