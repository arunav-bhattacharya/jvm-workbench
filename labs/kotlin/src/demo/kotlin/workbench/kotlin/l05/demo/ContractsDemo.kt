package workbench.kotlin.l05.demo

import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.InvocationKind
import kotlin.contracts.contract

sealed interface JobEvent
data class Printed(val jobId: String, val pages: Int) : JobEvent
data class Jammed(val jobId: String, val printer: String) : JobEvent

fun lookupPaper(printer: String): String? = if (printer.startsWith("laser-")) "a4" else null

/** Checks, but tells the compiler nothing. */
fun requirePaperPlain(paper: String?) {
    if (paper == null) throw IllegalArgumentException("paper size missing")
}

/** The same check, plus a promise: if this returns, paper was not null. */
@OptIn(ExperimentalContracts::class)
fun requirePaper(paper: String?) {
    contract { returns() implies (paper != null) }
    if (paper == null) throw IllegalArgumentException("paper size missing")
}

/** A promise about the receiver: a true result means this is a Printed. */
@OptIn(ExperimentalContracts::class)
fun JobEvent.isPrinted(): Boolean {
    contract { returns(true) implies (this@isPrinted is Printed) }
    return this is Printed
}

/** A promise about the lambda: it runs exactly once, during this call. */
@OptIn(ExperimentalContracts::class)
inline fun <T> once(block: () -> T): T {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return block()
}

fun main() {
    val paper = lookupPaper("laser-1")
    requirePaper(paper)
    println("paper = ${paper.uppercase()}")                  // smart cast to String

    val event: JobEvent = Printed("job-7", 12)
    if (event.isPrinted()) println("printed ${event.pages} pages")   // smart cast to Printed

    val label: String                                         // a val, assigned inside a lambda
    once { label = "job-17" }
    println("label = $label")

    // Wrong moves, one at a time. Predict the error, run, undo.
    // 1. Call requirePaperPlain(paper) instead of requirePaper(paper).
    // 2. Delete the line `contract { callsInPlace(...) }` in once.
    // 3. Delete @OptIn(ExperimentalContracts::class) above isPrinted.
}
