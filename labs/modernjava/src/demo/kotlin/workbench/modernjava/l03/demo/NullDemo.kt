package workbench.modernjava.l03.demo

data class Spot(val x: Int, val y: Int)
data class Segment(val from: Spot?, val to: Spot?)

// in Kotlin the type says whether null can arrive, and when compares with equals: null never throws
fun plainWhen(currency: String?): String = when (currency) {
    "EUR" -> "euro"
    else -> "other"                                 // null lands here
}

fun withNullWhen(currency: String?): String = when (currency) {
    null -> "missing"
    "EUR" -> "euro"
    else -> "other"
}

fun nullOrElse(o: Any?): String = when (o) {
    is String -> "text $o"
    else -> "null or other"
}

fun describeSegment(s: Segment): String {
    val from = s.from
    val to = s.to
    return when {
        from != null && to != null && from.x == to.x -> "vertical"
        else -> "other line $from -> $to"           // you write the null case yourself
    }
}

/** What when does with null: the nullable type decides, and nothing throws. */
fun main() {
    println("plainWhen(null):    ${plainWhen(null)}")
    println("withNullWhen(null): ${withNullWhen(null)}")
    println("nullOrElse:         ${nullOrElse(null)} / ${nullOrElse(42)}")
    println("line, null start:   ${describeSegment(Segment(null, Spot(1, 1)))}")
}
