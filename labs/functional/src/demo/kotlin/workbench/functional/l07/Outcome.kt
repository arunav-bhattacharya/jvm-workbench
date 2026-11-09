package workbench.functional.l07

/** A hand-written result type: a success holding a value, or a failure holding an error. */
sealed interface Outcome<out E, out A> {
    data class Ok<A>(val value: A) : Outcome<Nothing, A>
    data class Err<E>(val error: E) : Outcome<E, Nothing>
}

/** Change the value on the success track; a failure passes through untouched. */
inline fun <E, A, B> Outcome<E, A>.map(f: (A) -> B): Outcome<E, B> =
    when (this) { is Outcome.Ok -> Outcome.Ok(f(value)); is Outcome.Err -> this }

/** Run the next step that can fail, only on the success track. */
inline fun <E, A, B> Outcome<E, A>.andThen(f: (A) -> Outcome<E, B>): Outcome<E, B> =
    when (this) { is Outcome.Ok -> f(value); is Outcome.Err -> this }

sealed interface PayErr {
    data class Invalid(val why: String) : PayErr
    data object Declined : PayErr
}

data class Req(val amountMinor: Long, val currency: String)

fun validateReq(r: Req): Outcome<PayErr, Req> {
    println("  validate")
    return if (r.amountMinor > 0) Outcome.Ok(r) else Outcome.Err(PayErr.Invalid("amount<=0"))
}

fun authoriseReq(r: Req): Outcome<PayErr, String> {
    println("  authorise")
    return if (r.amountMinor < 10_000) Outcome.Ok("auth-1") else Outcome.Err(PayErr.Declined)
}

fun captureAuth(auth: String): Outcome<PayErr, String> {
    println("  capture")
    return Outcome.Ok("cap-of-$auth")
}

fun payReq(r: Req) = validateReq(r).andThen(::authoriseReq).andThen(::captureAuth).map { it.uppercase() }

fun main() {
    for (r in listOf(Req(500, "EUR"), Req(-1, "EUR"), Req(50_000, "EUR"))) {
        println("$r:")
        println("  -> ${payReq(r)}")
    }
}
