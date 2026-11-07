package workbench.generics.l07.demo

/** Wants a mutable list of anything at all, and adds to it. */
fun addMarker(list: MutableList<Any?>) {
    list.add("marker")
}

/** Wants a mutable list of some type it doesn't know. It can't add, but it can count. */
fun sizeOf(list: MutableList<*>): Int = list.size

fun main() {
    val anything: MutableList<Any?> = mutableListOf(1_200, "EUR", null)
    val ids: MutableList<String> = mutableListOf("pay_1")

    addMarker(anything)                         // fine: it really is a list of Any?
    println("anything = $anything, sizeOf(ids) = ${sizeOf(ids)}, sizeOf(anything) = ${sizeOf(anything)}")

    // Read-only List is covariant, so here * and Any? accept the same arguments:
    val a: List<Any?> = ids
    val b: List<*> = ids
    println("a = $a, b = $b")

    // Wrong move. Uncomment, predict the error, then run.
    // addMarker(ids)
}
