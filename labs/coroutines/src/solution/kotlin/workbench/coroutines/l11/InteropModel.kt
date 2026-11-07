package workbench.coroutines.l11

import java.util.concurrent.CompletableFuture

// Shared model. This file is the same in src/main and src/solution.

data class AuthRequest(val paymentId: String, val amountCents: Long)

enum class Decision { APPROVED, DECLINED }

/** A Java fraud client: returns at once with a future that completes when the score is ready. */
fun interface LegacyFraudClient {
    fun score(req: AuthRequest): CompletableFuture<Int>
}

data class Quote(val acquirer: String, val feeBasisPoints: Int)

/** A Kotlin quote source. Returns null when no acquirer will quote. */
fun interface QuoteSource {
    suspend fun quote(req: AuthRequest): Quote?
}
