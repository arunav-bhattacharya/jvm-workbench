package workbench.generics.l11

/**
 * A result that is either a failure (Left) or a success (Right). Both parameters are `out`:
 * an Either only hands its values out. Left fills R with Nothing, and Right fills L with Nothing,
 * so a Left<String> is an Either<String, R> for EVERY R. The declarations are done.
 */
sealed interface Either<out L, out R> {
    data class Left<out L>(val value: L) : Either<L, Nothing>
    data class Right<out R>(val value: R) : Either<Nothing, R>
}

/**
 * Applies [f] to a Right's value. A Left passes through unchanged.
 * TODO: use `when (this)`. In the Left branch you can return `this` itself: think about why it type-checks.
 */
fun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2> =
    TODO("is Either.Left -> this, is Either.Right -> Either.Right(f(value))")

/** The Right value, or [fallback] applied to the Left value. */
fun <L, R> Either<L, R>.getOrElse(fallback: (L) -> R): R =
    TODO("when (this) ...")
