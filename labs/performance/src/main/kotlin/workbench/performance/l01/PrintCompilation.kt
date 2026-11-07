package workbench.performance.l01

/**
 * One line of `-XX:+PrintCompilation` output, for example
 *
 * ```
 * 40   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
 * 60   27       4       workbench.performance.l01.Hot::total (42 bytes)   made not entrant: uncommon trap
 * ```
 */
data class CompileEvent(
    val millis: Long,              // milliseconds since the JVM started
    val compileId: Int,            // the same id appears again when this code is made not entrant
    val osr: Boolean,              // '%': on-stack replacement, compiled while a loop was running
    val synchronized: Boolean,     // 's'
    val exceptionHandler: Boolean, // '!': the method has a try/catch
    val native: Boolean,           // 'n': a native method wrapper
    val tier: Int?,                // 0 to 4, or null when tiered compilation is off
    val method: String,            // "workbench.performance.l01.Hot::longLoop"
    val osrBci: Int?,              // for OSR lines: the bytecode index of the loop, else null
    val bytes: Int?,               // size of the method's bytecode, null for "(native)"
    val madeNotEntrant: Boolean,   // the JVM stopped using this compiled code
    val reason: String?,           // JDK 25 prints "made not entrant: <reason>"; JDK 21 has no reason (null)
)

object PrintCompilation {

    /**
     * Parses one line. Returns null for anything that is not a compile line
     * (program output, blank lines, "Picked up ..." messages).
     *
     * The JVM prints: time, compile id, five attribute characters (`%`, `s`, `!`, `b`, `n` or a space),
     * the tier (only with tiered compilation), the method as `Class::name`, ` @ <bci>` for OSR,
     * `(N bytes)` or `(native)`, and an optional message such as `made not entrant`.
     */
    fun parse(line: String): CompileEvent? {
        TODO("parse one PrintCompilation line, or return null")
    }

    /** Parses every line and drops the ones that are not compile lines. */
    fun parseAll(lines: List<String>): List<CompileEvent> {
        TODO("parse each line, keep the non-null results")
    }

    /**
     * Methods that end the log with normal (non-OSR) C2 code still in use: a tier 4 compile
     * whose compile id never shows up again with "made not entrant".
     */
    fun runningInC2(events: List<CompileEvent>): Set<String> {
        TODO("tier 4, not OSR, and its compile id was never made not entrant")
    }

    /** Methods whose C2 code (tier 4, OSR or not) was thrown away at least once. */
    fun deoptimizedFromC2(events: List<CompileEvent>): Set<String> {
        TODO("tier 4 lines with madeNotEntrant")
    }
}
