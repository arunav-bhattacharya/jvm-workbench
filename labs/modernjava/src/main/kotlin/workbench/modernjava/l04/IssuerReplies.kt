package workbench.modernjava.l04

/**
 * TODO 4: read an untrusted reply into the model, at the edge of the service.
 * Never throw: return [Parsed.Rejected] with a short reason instead.
 *
 * - "APPROVED": needs an auth code and an amount, and must not carry a decline code
 *   (that reply contradicts itself). Becomes [AuthResult.Approved].
 * - "DECLINED": the decline code "51" is INSUFFICIENT_FUNDS, "62" is CARD_BLOCKED,
 *   "59" is SUSPECTED_FRAUD; any other code, or none, is OTHER.
 * - "SOFT_DECLINE": needs retryAfterSeconds. Becomes [AuthResult.RetryLater].
 * - anything else, including null: rejected.
 *
 * A value the model's own checks refuse (a bad auth code, a zero amount, a wait of 0 s)
 * must also come back as Rejected, not as an exception.
 */
fun parse(raw: RawReply): Parsed = TODO("parse")

/**
 * TODO 5: what the checkout page shows. One `when` over the result, no `else`:
 * - approved: "Payment approved."
 * - declined for insufficient funds: "Not enough funds. Try another card."
 * - declined as suspected fraud: "Payment declined. Please contact your bank."
 *   (never tell a possible fraudster why)
 * - any other decline: "Payment declined."
 * - retry later: "Your bank is busy. We'll try again in N seconds." with the whole seconds.
 */
fun customerMessage(result: AuthResult): String = TODO("customerMessage")
