package workbench.generics.l03

/**
 * A class in a tiny model of Kotlin's type system.
 *
 * [supers] are the direct superclasses and interfaces. [covariant] marks a class whose one type
 * parameter is declared `out`, the way `List<out E>` is. Lesson 4 of this track is about `out`;
 * here you only need to know that a covariant class lets its type argument vary upwards.
 */
class Klass(val name: String, val supers: List<Klass> = emptyList(), val covariant: Boolean = false) {
    override fun toString(): String = name
}

/**
 * A type: a class, its type arguments, and whether it is nullable.
 * `List<String>?` is `Type(list, listOf(Type(string)), nullable = true)`.
 *
 * One class gives many types: `Type(string)` and `Type(string, nullable = true)` are two types of one class.
 */
data class Type(val klass: Klass, val args: List<Type> = emptyList(), val nullable: Boolean = false) {
    override fun toString(): String =
        klass.name + (if (args.isEmpty()) "" else args.joinToString(", ", "<", ">")) + (if (nullable) "?" else "")
}

/**
 * SUBCLASSING: true when [sub] is [sup], or inherits from it directly or through other classes.
 * This is about classes only. It knows nothing about type arguments or nullability.
 */
fun isSubclass(sub: Klass, sup: Klass): Boolean =
    TODO("same class, or any of sub.supers is a subclass of sup")

/**
 * SUBTYPING: true when a value of type [sub] may be used wherever [sup] is expected.
 *
 * Apply three rules, in order:
 * 1. Nullability: a nullable type is never a subtype of a non-null type (`String?` is not a `String`).
 *    A non-null type is fine where a nullable one is expected (`String` is a `String?`).
 * 2. Classes: `sub.klass` must be a subclass of `sup.klass`.
 * 3. Type arguments: in this model, a generic class hands its arguments to its generic supertypes
 *    unchanged (`ArrayList<E> : MutableList<E> : List<E>`). So compare `sub.args[i]` with `sup.args[i]`
 *    for every argument of [sup], using the variance of `sup.klass`:
 *    - covariant: the sub argument must be a SUBTYPE of the sup argument;
 *    - invariant (the default): the two arguments must be EQUAL.
 *    If [sup] has no type arguments (like `Any`), there is nothing to compare.
 */
fun isSubtype(sub: Type, sup: Type): Boolean =
    TODO("apply the nullability, class and type-argument rules")
