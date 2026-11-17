package workbench.generics.l02.demo

/** Two bounds at once: T must be a CharSequence AND Comparable to itself. */
fun <T> sortedLabel(a: T, b: T): String where T : CharSequence, T : Comparable<T> =
    if (a < b) "$a (${a.length}) then $b (${b.length})" else "$b (${b.length}) then $a (${a.length})"

fun main() {
    println(sortedLabel("kiwi", "fig"))
    println(sortedLabel(StringBuilder("plum"), StringBuilder("lime")))   // does this compile? predict first

    // Wrong moves. Uncomment ONE at a time, predict the error, then run.
    // println(sortedLabel(42, 7))
    // fun <T> numberOrError(t: T) where T : Number, T : Exception {}
}
