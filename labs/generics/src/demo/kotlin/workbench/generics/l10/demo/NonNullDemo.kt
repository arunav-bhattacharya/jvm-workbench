package workbench.generics.l10.demo

/** T may be nullable (String?), but the result is "T, definitely not null". */
fun <T> List<T>.firstNotNullValue(): T & Any {
    for (item in this) if (item != null) return item     // smart cast: item is T & Any here
    throw NoSuchElementException("no non-null element")
}

/** The docs' example: fall back to a value that is known not to be null. */
fun <T> elvis(x: T, y: T & Any): T & Any = x ?: y

/** Implements the Java interface in NonNullDemoJava.java, whose methods are annotated @NotNull. */
class UpperCaser<T : CharSequence?> : NotNullTransformer<T> {
    @Suppress("UNCHECKED_CAST")
    override fun transform(value: T & Any): T & Any = value.toString().uppercase() as (T & Any)
}

fun main() {
    val currencies: List<String?> = listOf(null, "eur", "usd")
    val first: String = currencies.firstNotNullValue()      // T = String?, result String
    val note: String? = null
    val shown: String = elvis(note, "no note")
    println("first = $first, shown = $shown")
    println("transformed = ${UpperCaser<String?>().transform("pay_1")}")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // fun <T> forget(x: T): T & Any = x                    // 1
    // val n: String = UpperCaser<String?>().transform(null)   // 2
}

// 3. & Any needs a type parameter whose bound is nullable.
// fun <T : Any> pointless(x: T & Any) {}
