package workbench.coroutines.l06

// Shared model. This file is the same in src/main and src/solution.

enum class Channel { EMAIL, SMS, PUSH }

/** Sends one payment notification on one channel. Throws if the channel's gateway fails. */
fun interface Sender {
    suspend fun send(paymentId: String)
}

sealed interface Outcome {
    data object Delivered : Outcome
    data class Failed(val reason: String) : Outcome
}
