package workbench.generics.l10.demo

/** A new name for a function type. Not a new type: a Handler<E> IS an (E) -> Unit. */
typealias Handler<E> = (E) -> Unit

fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C = { a -> second(first(a)) }

fun fail(reason: String): Nothing = throw IllegalArgumentException(reason)

fun main() {
    // 1. Function1<in P, out R>: a more general second function fits.
    val parseCents: (String) -> Long = { it.replace(".", "").toLong() }
    val describe: (Any) -> String = { "<$it>" }
    val pipeline: (String) -> CharSequence = andThen(parseCents, describe)
    println("pipeline(\"12.50\") = ${pipeline("12.50")}")

    // 2. Nothing is a subtype of every type.
    val none: List<CardAuth> = emptyList()                  // emptyList() is a List<Nothing> here
    val cents: Long = "x".toLongOrNull() ?: 0L
    val strict: Long = "1200".toLongOrNull() ?: fail("not a number")   // fail returns Nothing, so this is a Long
    println("none = $none, cents = $cents, strict = $strict")

    // 3. A type alias is only a name.
    val audit: Handler<CardAuth> = { println("audit ${it.id}") }
    val plain: (CardAuth) -> Unit = audit                   // same type, no conversion
    plain(CardAuth("pay_1"))

    // Wrong move. Uncomment, predict the error, then run.
    // val tooStrict: (Any) -> String = andThen(parseCents, describe)
}

data class CardAuth(val id: String)
