package workbench.modernjava.l03.demo

data class Point(val x: Int, val y: Int)
data class Line(val from: Point, val to: Point)

sealed interface Outcome<out T> {
    data class Ok<T>(val value: T) : Outcome<T>
    data class Err(val message: String, val cause: Throwable?) : Outcome<Nothing>
}

data class Payment(val id: String, val amountMinor: Long)

// Kotlin can't take records apart in a when branch: match the outer type, then read the properties
fun describe(line: Line): String {
    val (from, to) = line                                  // positional destructuring via component1/2
    return when {
        from.x == to.x -> "vertical at x=${from.x} len ${kotlin.math.abs(to.y - from.y)}"
        from.y == to.y -> "horizontal at y=${from.y}"
        else -> "diagonal $from->$to"
    }
}

fun <T> show(r: Outcome<T>): String = when (r) {
    is Outcome.Ok -> "ok ${r.value}"
    is Outcome.Err if r.cause != null -> "err ${r.message} caused by ${r.cause::class.simpleName}"   // guard: Kotlin 2.2+
    is Outcome.Err -> "err ${r.message}"
}

/** The Kotlin side: smart casts and positional destructuring instead of record patterns. */
fun main() {
    println(describe(Line(Point(1, 0), Point(1, 5))))
    println(describe(Line(Point(0, 3), Point(7, 3))))
    println(describe(Line(Point(0, 0), Point(2, 2))))

    println(show(Outcome.Ok(listOf(1, 2))))
    println(show(Outcome.Err("boom", RuntimeException())))

    val o: Any = Line(Point(0, 0), Point(9, 9))
    if (o is Line && o.from.x == 0 && o.from.y == 0) {     // smart cast after the is check
        println("from origin to ${o.to}")
    }

    // destructuring goes by position, not by name: this compiles, with no warning, and swaps the values
    val (amountMinor, id) = Payment("p1", 500)
    println("swapped names: amountMinor=$amountMinor id=$id")
}
