package workbench.functional.l02

data class Payment(val id: String, val amountCents: Long, val currency: String, val country: String)

data class Rejection(val rule: String, val paymentId: String)

/** A rule looks at one payment. It returns a Rejection, or null when the payment passes. */
typealias Rule = (Payment) -> Rejection?

val SERVED_COUNTRIES = setOf("NL", "BE", "DE", "FR")
val SUPPORTED_CURRENCIES = setOf("EUR", "USD", "GBP")

// A closure: the returned lambda keeps limitCents alive after amountAtMost has returned.
fun amountAtMost(limitCents: Long): Rule = { p ->
    if (p.amountCents > limitCents) Rejection("amount-limit", p.id) else null
}

// A lambda stored in a val. It captures nothing, so it compiles to one shared instance.
val countryServed: Rule = { p ->
    if (p.country in SERVED_COUNTRIES) null else Rejection("country-not-served", p.id)
}

fun supportedCurrency(payment: Payment): Rejection? =
    if (payment.currency in SUPPORTED_CURRENCIES) null else Rejection("currency-not-supported", payment.id)

// A function reference: the type (Payment) -> Rejection? matches, so it IS a Rule.
val currencyRule: Rule = ::supportedCurrency

// firstNotNullOfOrNull is inline and stops at the first non-null result, so later rules never run.
fun firstRejection(payment: Payment, rules: List<Rule>): Rejection? =
    rules.firstNotNullOfOrNull { rule -> rule(payment) }

fun allRejections(payment: Payment, rules: List<Rule>): List<Rejection> =
    rules.mapNotNull { rule -> rule(payment) }

fun screen(payment: Payment, rules: List<Rule>, onReject: ((Rejection) -> Unit)? = null): Boolean {
    val rejection = firstRejection(payment, rules) ?: return true
    onReject?.invoke(rejection)        // a nullable function type is called with ?.invoke
    return false
}
