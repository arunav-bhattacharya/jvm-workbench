package workbench.generics.l11

sealed interface Either<out L, out R> {
    data class Left<out L>(val value: L) : Either<L, Nothing>
    data class Right<out R>(val value: R) : Either<Nothing, R>
}

// `is Left -> this` works because a Left<L> is an Either<L, Nothing>, and Nothing is a subtype of R2.
// Without `out` on Either, that line would not compile.
fun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2> = when (this) {
    is Either.Left -> this
    is Either.Right -> Either.Right(f(value))
}

fun <L, R> Either<L, R>.getOrElse(fallback: (L) -> R): R = when (this) {
    is Either.Left -> fallback(value)
    is Either.Right -> value
}
