package workbench.kotlin.l05

/** Where the clerks write what they decided. In the shop's app this could be a file or a table. */
fun interface Logbook {
    fun write(line: String)
}

/** The shift on duty. Its name goes on every line in the logbook. */
class Shift(val name: String)

/** A print job as it arrives at the counter, before anyone has checked it. */
data class JobRequest(val copies: Int, val paper: String?, val file: String?)

sealed interface Decision {
    data object Accepted : Decision
    data class Rejected(val code: String) : Decision
}

/** Writes [line] in the logbook, after the shift's name. Both come from the caller's context. */
context(logbook: Logbook, shift: Shift)
fun note(line: String) {
    logbook.write("[${shift.name}] $line")
}

/**
 * Checks the request against the shop's rules and writes one line in the logbook either way.
 * The Logbook and the Shift are context parameters: callers never pass them by hand,
 * and note(...) below receives them the same way.
 */
context(logbook: Logbook, shift: Shift)
fun JobRequest.review(maxCopies: Int): Decision =
    try {
        ensure(copies > 0, "COPIES_INVALID") { "copies must be positive, was $copies" }
        ensure(copies <= maxCopies, "TOO_MANY") { "copies $copies is over the limit $maxCopies" }
        ensure(paper != null, "PAPER_MISSING") { "a paper size is required" }
        ensure(file != null && file.endsWith(".pdf"), "FILE_MISSING") { "a PDF file is required" }
        // smart cast: the contract says ensure returned only because paper != null
        note("accepted $copies on ${paper.uppercase()}")
        Decision.Accepted
    } catch (e: JobRejected) {
        note("rejected ${e.code}: ${e.message}")
        Decision.Rejected(e.code)
    }
