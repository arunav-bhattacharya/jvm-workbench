package workbench.generics.l11.demo

/** Both parameters are out: an Either only hands values out. Left and Right fill the other side with Nothing. */
sealed interface Either<out L, out R> {
    data class Left<out L>(val value: L) : Either<L, Nothing>
    data class Right<out R>(val value: R) : Either<Nothing, R>
}

/** Maps the failure side. `is Right -> this` type-checks because a Right<R> is an Either<Nothing, R>. */
fun <L, R, L2> Either<L, R>.mapLeft(f: (L) -> L2): Either<L2, R> = when (this) {
    is Either.Left -> Either.Left(f(value))
    is Either.Right -> this
}

fun <L, R, T> Either<L, R>.fold(onLeft: (L) -> T, onRight: (R) -> T): T = when (this) {
    is Either.Left -> onLeft(value)
    is Either.Right -> onRight(value)
}

fun parseCents(text: String): Either<String, Long> =
    text.toLongOrNull()?.let { Either.Right(it) } ?: Either.Left("not a number: $text")

fun main() {
    val ok = parseCents("1200")
    val bad = parseCents("12,00")
    println(ok.fold({ "error: $it" }, { "cents: $it" }))
    println(bad.mapLeft { it.uppercase() })

    val wider: Either<Any, Number> = ok          // out on both sides: String -> Any, Long -> Number
    println("wider = $wider")

    // Break it: remove both `out`s from `sealed interface Either` (keep them on Left and Right),
    // run, and read the errors in mapLeft and on the `wider` line.
}
