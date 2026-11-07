package workbench.generics.l10

abstract class PaymentRequestBuilder<B : PaymentRequestBuilder<B>> {
    protected var cents: Long = 0
    protected var currency: String? = null
    protected var reference: String = ""

    // each setter returns self(): typed B, so the chain keeps the subclass type
    fun amount(cents: Long): B { this.cents = cents; return self() }
    fun currency(code: String): B { currency = code; return self() }
    fun reference(text: String): B { reference = text; return self() }

    protected abstract fun self(): B

    protected fun checkCommon() {
        check(cents > 0) { "amount must be positive" }
        check(currency != null) { "currency is required" }
    }
}

class CardPaymentBuilder : PaymentRequestBuilder<CardPaymentBuilder>() {
    private var token: String? = null

    fun cardToken(token: String): CardPaymentBuilder { this.token = token; return this }

    override fun self(): CardPaymentBuilder = this      // no cast needed: B is CardPaymentBuilder here

    fun build(): CardPayment {
        checkCommon()
        val t = checkNotNull(token) { "card token is required" }
        return CardPayment(cents, currency!!, reference, t)
    }
}

class BankTransferBuilder : PaymentRequestBuilder<BankTransferBuilder>() {
    private var iban: String? = null

    fun iban(iban: String): BankTransferBuilder { this.iban = iban; return this }

    override fun self(): BankTransferBuilder = this

    fun build(): BankTransfer {
        checkCommon()
        val i = checkNotNull(iban) { "iban is required" }
        return BankTransfer(cents, currency!!, reference, i)
    }
}
