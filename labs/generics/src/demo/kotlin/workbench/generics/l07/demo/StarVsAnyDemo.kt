package workbench.generics.l07.demo

/** Wants a mutable list of anything at all, and adds to it. */
fun addPriceTag(list: MutableList<Any?>) {
    list.add("price tag")
}

/** Wants a mutable list of some type it doesn't know. It can't add, but it can count. */
fun countItems(list: MutableList<*>): Int = list.size

fun main() {
    val drawer: MutableList<Any?> = mutableListOf("pencil", 3, null)     // the drawer of odds and ends
    val varieties: MutableList<String> = mutableListOf("Gala")

    addPriceTag(drawer)                          // fine: it really is a list of Any?
    println("drawer = $drawer, countItems(varieties) = ${countItems(varieties)}, countItems(drawer) = ${countItems(drawer)}")

    // Read-only List is covariant, so here * and Any? accept the same arguments:
    val a: List<Any?> = varieties
    val b: List<*> = varieties
    println("a = $a, b = $b")

    // Wrong move. Uncomment, predict the error, then run.
    // addPriceTag(varieties)
}
