package workbench.kotlin.l05

/** Where audit lines go. In a service this would write to a table or a topic. */
fun interface AuditLog {
    fun record(line: String)
}

/** The transaction being processed. */
class TxContext(val txId: String)

data class AuthRequest(val amountMinor: Long, val currency: String?, val cardToken: String?)

sealed interface Decision {
    data object Approved : Decision
    data class Rejected(val code: String) : Decision
}

/** Records [line] prefixed with the transaction id. Both come from the caller's context. */
context(audit: AuditLog, tx: TxContext)
fun note(line: String) {
    audit.record("[${tx.txId}] $line")
}

/**
 * Checks the request against the rules and records one audit line either way.
 * The AuditLog and the TxContext are context parameters: callers never pass them by hand,
 * and note(...) below receives them the same way.
 */
context(audit: AuditLog, tx: TxContext)
fun AuthRequest.authorize(limitMinor: Long): Decision =
    try {
        ensure(amountMinor > 0, "AMOUNT_INVALID") { "amount must be positive, was $amountMinor" }
        ensure(amountMinor <= limitMinor, "OVER_LIMIT") { "amount $amountMinor is over the limit $limitMinor" }
        ensure(currency != null, "CURRENCY_MISSING") { "currency is required" }
        ensure(cardToken != null && cardToken.startsWith("tok_"), "CARD_MISSING") { "a card token is required" }
        // smart cast: the contract says ensure returned only because currency != null
        note("approved $amountMinor ${currency.uppercase()}")
        Decision.Approved
    } catch (e: PaymentRejected) {
        note("rejected ${e.code}: ${e.message}")
        Decision.Rejected(e.code)
    }
