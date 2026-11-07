package workbench.generics.l08

/**
 * Turns text into typed values: "12.50 EUR" into a Money, "2026-03-01" into a LocalDate.
 * One parser per target class, keyed by a Class token, the way a Java API would do it.
 */
class Parsers {
    private val byType = HashMap<Class<*>, (String) -> Any>()

    /** Registers [parser] for [type]. A later registration for the same type replaces it. */
    fun <T : Any> register(type: Class<T>, parser: (String) -> T) {
        byType[type] = parser
    }

    /**
     * Parses [text] into a [type]. Java callers use this one: `parsers.parse("12.50 EUR", Money.class)`.
     *
     * TODO 3: look up the parser for [type]. If there is none, throw
     * IllegalArgumentException("no parser for " + type.simpleName). Otherwise call it and return the
     * result as a T with `type.cast(...)` (a checked cast, no warning).
     */
    fun <T : Any> parse(text: String, type: Class<T>): T =
        TODO("look up the parser, call it, cast with type.cast")

    /**
     * The Kotlin-friendly version: `parsers.parse<Money>("12.50 EUR")`.
     *
     * TODO 4: make it inline with a reified T, and pass `T::class.java` to the version above.
     */
    fun <T : Any> parse(text: String): T = TODO("inline + reified, then call parse(text, T::class.java)")
}
