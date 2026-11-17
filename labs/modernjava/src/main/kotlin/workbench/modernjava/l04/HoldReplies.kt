package workbench.modernjava.l04

/**
 * TODO 4: read an untrusted reply into the model, at the edge of the program.
 * Never throw: return [Parsed.Rejected] with a short reason instead.
 *
 * - "READY": needs a pickup code and a hold shelf, and must not carry a reason code
 *   (that reply contradicts itself). Becomes [HoldResult.Ready].
 * - "UNAVAILABLE": the reason code "10" is LOST, "20" is NOT_IN_CATALOGUE,
 *   "30" is ACCOUNT_BLOCKED; any other code, or none, is OTHER.
 * - "WAITLISTED": needs waitDays. Becomes [HoldResult.Waitlisted].
 * - anything else, including null: rejected.
 *
 * A value the model's own checks refuse (a bad pickup code, shelf 0, a wait of 0 days)
 * must also come back as Rejected, not as an exception.
 */
fun parse(raw: RawReply): Parsed = TODO("parse")

/**
 * TODO 5: what the screen at the self-service desk shows. One `when` over the result, no `else`:
 * - ready: "Your book is waiting on hold shelf N."
 * - unavailable, not in the catalogue: "We don't have this title. Ask us to order it."
 * - unavailable, account blocked: "Please ask at the desk."
 *   (other people can read this screen, so it never says what is wrong with an account)
 * - any other unavailable: "This title is not available right now."
 * - waitlisted: "You're on the waiting list. Expected wait: N days." with the whole days.
 */
fun screenMessage(result: HoldResult): String = TODO("screenMessage")
