package workbench.functional.l02.demo

data class Payment(val id: String, val amountCents: Long, val currency: String, val country: String)
data class Rejection(val rule: String, val paymentId: String)

// A rule is a function from a payment to a rejection, or null when the payment passes.
typealias Rule = (Payment) -> Rejection?

// Each rule is a value: a lambda stored in a val, ready to go into a list.
val maxAmount: Rule = { p -> if (p.amountCents > 500_000) Rejection("amount-limit", p.id) else null }
val servedCountry: Rule = { p -> if (p.country in setOf("NL", "BE", "DE")) null else Rejection("country-not-served", p.id) }
val euroOnly: Rule = { p -> if (p.currency == "EUR") null else Rejection("currency-not-supported", p.id) }
val noMicroPayments: Rule = { p -> if (p.amountCents < 100) Rejection("micro-payment", p.id) else null }

// Different merchants get different lists. Adding a rule for one merchant changes nothing above.
val standardRules: List<Rule> = listOf(maxAmount, servedCountry, euroOnly)
val marketplaceRules: List<Rule> = standardRules + noMicroPayments

// Run the rules in order and stop at the first rejection.
fun firstRejection(p: Payment, rules: List<Rule>): Rejection? = rules.firstNotNullOfOrNull { rule -> rule(p) }

fun main() {
    val payments = listOf(
        Payment("pay_1", 12_000, "EUR", "NL"),
        Payment("pay_2", 900_000, "EUR", "DE"),
        Payment("pay_3", 50, "EUR", "BE"),
        Payment("pay_4", 4_000, "USD", "US"),
    )
    for (p in payments) {
        val standard = firstRejection(p, standardRules)?.rule ?: "ok"
        val marketplace = firstRejection(p, marketplaceRules)?.rule ?: "ok"
        println("${p.id}: standard=$standard, marketplace=$marketplace")
    }
}
