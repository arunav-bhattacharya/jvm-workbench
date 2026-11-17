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

/**
 * TODO 3: write "[<shift name>] <line>" in the logbook. Both values are context parameters: use them by name.
 */
context(logbook: Logbook, shift: Shift)
fun note(line: String) {
    TODO("logbook.write(...)")
}

/**
 * TODO 4: check the request with ensure, in this order, and return a Decision:
 *  - copies > 0, else code COPIES_INVALID
 *  - copies <= maxCopies, else code TOO_MANY, message "copies <c> is over the limit <max>"
 *  - paper != null, else code PAPER_MISSING
 *  - file is not null and ends with ".pdf", else code FILE_MISSING
 * On success call note("accepted <copies> on <PAPER in upper case>") and return Decision.Accepted.
 * On JobRejected call note("rejected <code>: <message>") and return Decision.Rejected(code).
 * Write paper.uppercase() without !! or ?. : it compiles once ensure has its contract.
 */
context(logbook: Logbook, shift: Shift)
fun JobRequest.review(maxCopies: Int): Decision = TODO("ensure the rules, note the result")
