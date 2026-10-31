package workbench.generics.l06

// from: only read  -> out-projection, a MutableList<Int> fits a MutableList<out Number>
// to:   only written -> in-projection, a MutableList<Number> fits a MutableList<in Int>
fun <T> copyInto(from: MutableList<out T>, to: MutableList<in T>): Int {
    for (x in from) to.add(x)   // reading from `from` gives T; adding a T to `to` is allowed
    return from.size
}

fun <T> fillWith(target: MutableList<in T>, value: T, count: Int) {
    repeat(count) { target.add(value) }
}

// List is already covariant: List<out Number> here would only earn a "projection is redundant" warning
fun sumAll(amounts: List<Number>): Double {
    var sum = 0.0
    for (a in amounts) sum += a.toDouble()
    return sum
}
