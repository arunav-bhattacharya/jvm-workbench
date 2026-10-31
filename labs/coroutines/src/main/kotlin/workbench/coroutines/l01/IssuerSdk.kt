package workbench.coroutines.l01

// The card issuer's SDK. It is callback-based, like many payment SDKs, and you cannot change it.
// This file is the same in src/main and src/solution.

/** What we ask the issuer to approve. */
data class AuthRequest(val cardToken: String, val amountCents: Long)

/** The issuer's answer when it approves. */
data class Authorization(val approvalCode: String, val amountCents: Long)

/** The issuer said no. */
class IssuerDeclinedException(val reason: String) : Exception("declined: $reason")

/** Exactly one of these is called, later, on one of the SDK's own threads. */
interface AuthCallback {
    fun onApproved(auth: Authorization)
    fun onFailed(error: Throwable)
}

/** A handle to a request in flight. */
fun interface InFlight {
    /** Asks the issuer to drop the request. A late reply may still arrive after this. */
    fun cancel()
}

interface CardIssuerClient {
    /** Starts an authorization and returns at once. The answer comes through [callback]. */
    fun authorize(request: AuthRequest, callback: AuthCallback): InFlight
}
