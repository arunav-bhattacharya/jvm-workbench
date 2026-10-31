package workbench.generics.l03

class Klass(val name: String, val supers: List<Klass> = emptyList(), val covariant: Boolean = false) {
    override fun toString(): String = name
}

data class Type(val klass: Klass, val args: List<Type> = emptyList(), val nullable: Boolean = false) {
    override fun toString(): String =
        klass.name + (if (args.isEmpty()) "" else args.joinToString(", ", "<", ">")) + (if (nullable) "?" else "")
}

// subclassing walks the inheritance graph and nothing else
fun isSubclass(sub: Klass, sup: Klass): Boolean =
    sub === sup || sub.supers.any { isSubclass(it, sup) }

fun isSubtype(sub: Type, sup: Type): Boolean {
    // 1. String? may hold null, so it can't stand in for String; String can stand in for String?
    if (sub.nullable && !sup.nullable) return false
    // 2. the classes must be related by inheritance
    if (!isSubclass(sub.klass, sup.klass)) return false
    // 3. type arguments, compared with the variance of the class we are checking against
    for (i in sup.args.indices) {
        val a = sub.args.getOrNull(i) ?: return false
        val b = sup.args[i]
        val ok = if (sup.klass.covariant) isSubtype(a, b)   // List<String> is a List<Any>
                 else a == b                                // MutableList<String> is NOT a MutableList<Any>
        if (!ok) return false
    }
    return true
}
