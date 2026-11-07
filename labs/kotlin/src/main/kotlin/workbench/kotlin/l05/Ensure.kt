package workbench.kotlin.l05

/** A business rule said no. [code] is stable and goes to the client; the message is for humans. */
class PaymentRejected(val code: String, message: String) : RuntimeException(message)

/**
 * Like require, for payment rules: throws PaymentRejected(code, lazyMessage()) when [condition] is false.
 *
 * TODO 1: write the body. Call lazyMessage only when you throw.
 * TODO 2: add a contract as the first statement, so that
 *  - after ensure returns, the compiler knows condition was true (returns() implies condition)
 *  - the compiler knows lazyMessage runs at most once, in place (callsInPlace with InvocationKind.AT_MOST_ONCE)
 * Contracts are Experimental in Kotlin 2.4: you need @OptIn(ExperimentalContracts::class) and the
 * imports kotlin.contracts.contract, kotlin.contracts.InvocationKind and kotlin.contracts.ExperimentalContracts.
 */
inline fun ensure(condition: Boolean, code: String, lazyMessage: () -> String) {
    TODO("throw PaymentRejected when the condition is false")
}
