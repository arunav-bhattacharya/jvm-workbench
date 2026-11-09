package workbench.functional.l06

import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.InvocationKind
import kotlin.contracts.contract

data class Authorization(val code: String, val amountMinor: Long)

fun authorize(amountMinor: Long) = Authorization("A-${amountMinor % 997}", amountMinor)

// a hand-written also: not inline, no contract
fun <T> T.plainAlso(block: (T) -> Unit): T { block(this); return this }

// the same plus what the stdlib adds: inline and an EXACTLY_ONCE contract
@OptIn(ExperimentalContracts::class)
inline fun <T> T.contractAlso(block: (T) -> Unit): T {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    block(this)
    return this
}

fun main() {
    val code1: String
    val auth1 = authorize(1_999).also { code1 = it.code }          // the stdlib's also: compiles
    println("also:         $code1 for ${auth1.amountMinor}")

    val code2: String
    val auth2 = authorize(4_250).contractAlso { code2 = it.code }  // yours, with the contract: compiles
    println("contractAlso: $code2 for ${auth2.amountMinor}")

    // Uncomment the next two lines and run again. The compiler can't know how often plainAlso calls the block.
    // val code3: String
    // authorize(700).plainAlso { code3 = it.code }
}
