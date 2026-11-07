package workbench.generics.l10

/**
 * A fluent builder hierarchy. The common setters live in the base class, and each one must return
 * the SUBCLASS type, so that `CardPaymentBuilder().amount(1_200).cardToken("tok_1")` keeps going.
 *
 * The recursive bound `B : PaymentRequestBuilder<B>` is how the base class names "my own subclass".
 * Each subclass passes itself: `class CardPaymentBuilder : PaymentRequestBuilder<CardPaymentBuilder>()`.
 * The signatures are done. Write the bodies.
 */
abstract class PaymentRequestBuilder<B : PaymentRequestBuilder<B>> {
    protected var cents: Long = 0
    protected var currency: String? = null
    protected var reference: String = ""

    /** Sets the amount in minor units and returns this builder, typed as the subclass. */
    fun amount(cents: Long): B = TODO("store it, then return self()")

    /** Sets the ISO currency code, such as "EUR". */
    fun currency(code: String): B = TODO("store it, then return self()")

    /** Sets the free-text reference. Optional: it defaults to "". */
    fun reference(text: String): B = TODO("store it, then return self()")

    /** `this`, typed as the subclass. Each subclass implements it as `= this`. */
    protected abstract fun self(): B

    /**
     * Checks the common fields before a subclass builds:
     * throws IllegalStateException("amount must be positive") if cents <= 0,
     * and IllegalStateException("currency is required") if no currency was set.
     */
    protected fun checkCommon() {
        TODO("use check(...) twice")
    }
}

class CardPaymentBuilder : PaymentRequestBuilder<CardPaymentBuilder>() {
    private var token: String? = null

    fun cardToken(token: String): CardPaymentBuilder = TODO("store it, return this")

    override fun self(): CardPaymentBuilder = TODO("return this")

    /** Checks the common fields, then IllegalStateException("card token is required"), then builds. */
    fun build(): CardPayment = TODO("checkCommon(), check the token, build the CardPayment")
}

class BankTransferBuilder : PaymentRequestBuilder<BankTransferBuilder>() {
    private var iban: String? = null

    fun iban(iban: String): BankTransferBuilder = TODO("store it, return this")

    override fun self(): BankTransferBuilder = TODO("return this")

    /** Checks the common fields, then IllegalStateException("iban is required"), then builds. */
    fun build(): BankTransfer = TODO("checkCommon(), check the iban, build the BankTransfer")
}
