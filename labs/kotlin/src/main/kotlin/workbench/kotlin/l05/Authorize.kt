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

/**
 * TODO 3: record "[<txId>] <line>" in the audit log. Both values are context parameters: use them by name.
 */
context(audit: AuditLog, tx: TxContext)
fun note(line: String) {
    TODO("audit.record(...)")
}

/**
 * TODO 4: check the request with ensure, in this order, and return a Decision:
 *  - amountMinor > 0, else code AMOUNT_INVALID
 *  - amountMinor <= limitMinor, else code OVER_LIMIT, message "amount <a> is over the limit <l>"
 *  - currency != null, else code CURRENCY_MISSING
 *  - cardToken is not null and starts with "tok_", else code CARD_MISSING
 * On success call note("approved <amountMinor> <CURRENCY in upper case>") and return Decision.Approved.
 * On PaymentRejected call note("rejected <code>: <message>") and return Decision.Rejected(code).
 * Write currency.uppercase() without !! or ?. : it compiles once ensure has its contract.
 */
context(audit: AuditLog, tx: TxContext)
fun AuthRequest.authorize(limitMinor: Long): Decision = TODO("ensure the rules, note the result")
