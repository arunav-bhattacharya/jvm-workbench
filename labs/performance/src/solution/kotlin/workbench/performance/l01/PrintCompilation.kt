package workbench.performance.l01

data class CompileEvent(
    val millis: Long,
    val compileId: Int,
    val osr: Boolean,
    val synchronized: Boolean,
    val exceptionHandler: Boolean,
    val native: Boolean,
    val tier: Int?,
    val method: String,
    val osrBci: Int?,
    val bytes: Int?,
    val madeNotEntrant: Boolean,
    val reason: String?,
)

object PrintCompilation {

    // time, id, then exactly five attribute characters, then an optional tier digit,
    // then the method, an optional " @ bci", and "(N bytes)" or "(native)"; the rest is the message
    private val LINE = Regex(
        """^\s*(\d+)\s+(\d+) ([%s!bn ]{5}) (?:([0-4-]) )?\s*(\S+)(?: @ (\d+))? \((?:(\d+) bytes|native)\)(.*)$"""
    )

    fun parse(line: String): CompileEvent? {
        val m = LINE.matchEntire(line) ?: return null
        val (time, id, attrs, tier, method, bci, bytes, rest) = m.destructured
        val message = rest.trim()
        val notEntrant = message.startsWith("made not entrant")
        return CompileEvent(
            millis = time.toLong(),
            compileId = id.toInt(),
            osr = attrs[0] == '%',
            synchronized = attrs[1] == 's',
            exceptionHandler = attrs[2] == '!',
            native = attrs[4] == 'n',
            tier = tier.toIntOrNull(),                       // "" (non-tiered) and "-" both become null
            method = method,
            osrBci = bci.toIntOrNull(),
            bytes = bytes.toIntOrNull(),                     // empty for "(native)"
            madeNotEntrant = notEntrant,
            // JDK 25: "made not entrant: uncommon trap"; JDK 21: just "made not entrant"
            reason = if (notEntrant) message.substringAfter(":", "").trim().ifEmpty { null } else null,
        )
    }

    fun parseAll(lines: List<String>): List<CompileEvent> = lines.mapNotNull(::parse)

    fun runningInC2(events: List<CompileEvent>): Set<String> {
        val dead = events.filter { it.madeNotEntrant }.map { it.compileId }.toSet()
        return events
            .filter { it.tier == 4 && !it.osr && !it.madeNotEntrant && it.compileId !in dead }
            .map { it.method }
            .toSet()
    }

    fun deoptimizedFromC2(events: List<CompileEvent>): Set<String> =
        events.filter { it.tier == 4 && it.madeNotEntrant }.map { it.method }.toSet()
}
