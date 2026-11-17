package workbench.kotlin.l05

import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.InvocationKind
import kotlin.contracts.contract

/** A shop rule said no. [code] is stable and goes back to the customer's screen; the message is for people. */
class JobRejected(val code: String, message: String) : RuntimeException(message)

/**
 * Like require, for the shop's rules: throws JobRejected(code, lazyMessage()) when [condition] is false.
 *
 * The contract states two facts the compiler can't work out alone:
 *  - if ensure returns normally, condition was true (so callers get smart casts after it)
 *  - lazyMessage runs at most once, and only during this call
 * The compiler trusts both without checking them, so they must be true.
 */
@OptIn(ExperimentalContracts::class)
inline fun ensure(condition: Boolean, code: String, lazyMessage: () -> String) {
    contract {
        returns() implies condition
        callsInPlace(lazyMessage, InvocationKind.AT_MOST_ONCE)
    }
    if (!condition) throw JobRejected(code, lazyMessage())
}
