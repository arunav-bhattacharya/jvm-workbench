package workbench.functional.l06.demo

import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.InvocationKind
import kotlin.contracts.contract

data class Jar(val label: String, val grams: Int)

/** Fills a jam jar and prints a label for it. */
fun fillJar(grams: Int) = Jar("J-${grams % 97}", grams)

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
    val label1: String
    val jar1 = fillJar(450).also { label1 = it.label }          // the stdlib's also: compiles
    println("also:         $label1 for ${jar1.grams} g")

    val label2: String
    val jar2 = fillJar(300).contractAlso { label2 = it.label }  // yours, with the contract: compiles
    println("contractAlso: $label2 for ${jar2.grams} g")

    // Uncomment the next two lines and run again. The compiler can't know how often plainAlso calls the block.
    // val label3: String
    // fillJar(250).plainAlso { label3 = it.label }
}
