package workbench.generics.l01

data class Duo<A, B>(val first: A, val second: B) {

    // second is a B and first is an A, so Duo(second, first) is a Duo<B, A>
    fun swap(): Duo<B, A> = Duo(second, first)

    // f turns a B into a C; C is fixed by the lambda the caller passes
    fun <C> mapSecond(f: (B) -> C): Duo<A, C> = Duo(first, f(second))
}

fun <A, B> zipToDuos(left: List<A>, right: List<B>): List<Duo<A, B>> {
    val n = minOf(left.size, right.size)
    val out = ArrayList<Duo<A, B>>(n)
    for (i in 0 until n) out.add(Duo(left[i], right[i]))
    return out
}
