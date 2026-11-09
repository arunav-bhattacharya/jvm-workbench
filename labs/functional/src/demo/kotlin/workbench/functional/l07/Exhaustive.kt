package workbench.functional.l07

/** The expected ways an authorization can fail. A closed set: the compiler knows every case. */
sealed interface AuthFailure {
    data class InvalidAmount(val amountMinor: Long) : AuthFailure
    data object CardExpired : AuthFailure
    data class InsufficientFunds(val shortByMinor: Long) : AuthFailure
    // Uncomment the next line and run again.
    // data class FraudSuspected(val score: Int) : AuthFailure
}

sealed interface AuthResult {
    data class Approved(val code: String) : AuthResult
    data class Refused(val reason: AuthFailure) : AuthResult
}

/** The signature now says it can fail, and how. Nothing is thrown for a decline. */
fun authorizeCard(amountMinor: Long, balanceMinor: Long, expiryYear: Int): AuthResult = when {
    amountMinor <= 0 -> AuthResult.Refused(AuthFailure.InvalidAmount(amountMinor))
    expiryYear < 2026 -> AuthResult.Refused(AuthFailure.CardExpired)
    amountMinor > balanceMinor -> AuthResult.Refused(AuthFailure.InsufficientFunds(amountMinor - balanceMinor))
    else -> AuthResult.Approved("A-${amountMinor % 997}")
}

/** The one place that knows HTTP: an exhaustive when with no else branch. */
fun httpStatus(failure: AuthFailure): Int = when (failure) {
    is AuthFailure.InvalidAmount -> 400
    AuthFailure.CardExpired -> 402
    is AuthFailure.InsufficientFunds -> 402
}

fun main() {
    val attempts = listOf(Triple(4_250L, 10_000L, 2028), Triple(-5L, 10_000L, 2028), Triple(4_250L, 10_000L, 2024), Triple(14_250L, 10_000L, 2028))
    for ((amount, balance, expiry) in attempts) {
        val line = when (val result = authorizeCard(amount, balance, expiry)) {
            is AuthResult.Approved -> "200 approved ${result.code}"
            is AuthResult.Refused -> "${httpStatus(result.reason)} ${result.reason}"
        }
        println(line)
    }
}
