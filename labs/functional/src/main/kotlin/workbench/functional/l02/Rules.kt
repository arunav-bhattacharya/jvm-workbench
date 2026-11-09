package workbench.functional.l02

data class Payment(val id: String, val amountCents: Long, val currency: String, val country: String)

data class Rejection(val rule: String, val paymentId: String)

/** A rule looks at one payment. It returns a Rejection, or null when the payment passes. */
typealias Rule = (Payment) -> Rejection?

val SERVED_COUNTRIES = setOf("NL", "BE", "DE", "FR")
val SUPPORTED_CURRENCIES = setOf("EUR", "USD", "GBP")

/**
 * TODO 1: return a rule that rejects payments above [limitCents] with rule name "amount-limit".
 * A payment of exactly limitCents passes. The lambda you return captures limitCents: that's a closure.
 */
fun amountAtMost(limitCents: Long): Rule = TODO("return a lambda that compares it.amountCents with limitCents")

/**
 * TODO 2: a rule written as a lambda value. Reject payments whose country is not in SERVED_COUNTRIES,
 * with rule name "country-not-served".
 */
val countryServed: Rule = { TODO("check it.country against SERVED_COUNTRIES") }

/** TODO 3a: an ordinary function. Reject currencies outside SUPPORTED_CURRENCIES with rule name "currency-not-supported". */
fun supportedCurrency(payment: Payment): Rejection? = TODO("an ordinary if expression")

/** TODO 3b: make this a function reference to supportedCurrency instead of a lambda. */
val currencyRule: Rule = { TODO("replace this lambda with ::supportedCurrency") }

/**
 * TODO 4: run [rules] in order and return the first rejection, or null if every rule passes.
 * Stop at the first rejection: later rules must not run (some of them call a fraud API).
 */
fun firstRejection(payment: Payment, rules: List<Rule>): Rejection? = TODO("loop, or look for firstNotNullOfOrNull")

/** TODO 5: run every rule and return all the rejections, in rule order. */
fun allRejections(payment: Payment, rules: List<Rule>): List<Rejection> = TODO("every non-null result")

/**
 * TODO 6: screen a payment. Returns true when it passes every rule. When it is rejected, call
 * [onReject] with the first rejection (if a callback was given) and return false.
 * onReject has a nullable function type: callers may leave it out.
 */
fun screen(payment: Payment, rules: List<Rule>, onReject: ((Rejection) -> Unit)? = null): Boolean =
    TODO("firstRejection, then onReject?.invoke(...)")
