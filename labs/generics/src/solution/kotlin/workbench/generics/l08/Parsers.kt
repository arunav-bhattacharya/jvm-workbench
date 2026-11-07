package workbench.generics.l08

class Parsers {
    private val byType = HashMap<Class<*>, (String) -> Any>()

    fun <T : Any> register(type: Class<T>, parser: (String) -> T) {
        byType[type] = parser
    }

    // the Java-style core: the caller passes the class, because T is erased in here
    fun <T : Any> parse(text: String, type: Class<T>): T {
        val parser = byType[type] ?: throw IllegalArgumentException("no parser for " + type.simpleName)
        return type.cast(parser(text))                       // checked at run time, no unchecked warning
    }

    // the Kotlin wrapper: the compiler writes Money::class.java into each call site for you
    inline fun <reified T : Any> parse(text: String): T = parse(text, T::class.java)
}
