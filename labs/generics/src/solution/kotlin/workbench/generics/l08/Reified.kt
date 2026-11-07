package workbench.generics.l08

// inline: the body is copied into each caller; reified: the caller's real T is copied in with it
inline fun <reified T> Any?.asOrNull(): T? = this as? T     // a real instanceof check, no warning

inline fun <reified T> instancesOf(items: Iterable<*>): List<T> {
    val out = ArrayList<T>()
    for (item in items) if (item is T) out += item           // `is T` works only because T is reified
    return out
}
