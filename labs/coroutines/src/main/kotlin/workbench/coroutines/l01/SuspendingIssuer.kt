package workbench.coroutines.l01

/**
 * Calls [CardIssuerClient.authorize] and suspends until the issuer answers.
 *
 * - Returns the [Authorization] when the issuer approves.
 * - Throws the error the issuer reports (for example [IssuerDeclinedException]).
 * - If the calling coroutine is cancelled while it waits, calls [InFlight.cancel] on the
 *   request, so the issuer can drop it. A late reply after that must be ignored.
 *
 * Use `suspendCancellableCoroutine`, not `suspendCoroutine`.
 */
suspend fun CardIssuerClient.authorizeAwait(request: AuthRequest): Authorization {
    TODO("wrap authorize(request, callback) with suspendCancellableCoroutine")
}
