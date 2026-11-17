package workbench.functional.l07.demo

/** A hand-written result type: a success holding a value, or a failure holding an error. */
sealed interface Outcome<out E, out A> {
    data class Ok<A>(val value: A) : Outcome<Nothing, A>
    data class Err<E>(val error: E) : Outcome<E, Nothing>
}

/** Change the value on the success track; a failure passes through untouched. */
inline fun <E, A, B> Outcome<E, A>.map(f: (A) -> B): Outcome<E, B> =
    when (this) { is Outcome.Ok -> Outcome.Ok(f(value)); is Outcome.Err -> this }

/** Run the next step that can fail, only on the success track. */
inline fun <E, A, B> Outcome<E, A>.andThen(f: (A) -> Outcome<E, B>): Outcome<E, B> =
    when (this) { is Outcome.Ok -> f(value); is Outcome.Err -> this }

sealed interface BakeErr {
    data class Invalid(val why: String) : BakeErr
    data object BowlTooSmall : BakeErr
}

data class Batter(val flourGrams: Int)

fun checkBatter(b: Batter): Outcome<BakeErr, Batter> {
    println("  check")
    return if (b.flourGrams > 0) Outcome.Ok(b) else Outcome.Err(BakeErr.Invalid("flour<=0"))
}

fun mix(b: Batter): Outcome<BakeErr, String> {
    println("  mix")
    return if (b.flourGrams <= 1_000) Outcome.Ok("dough") else Outcome.Err(BakeErr.BowlTooSmall)
}

fun bake(dough: String): Outcome<BakeErr, String> {
    println("  bake")
    return Outcome.Ok("loaf from $dough")
}

fun makeLoaf(b: Batter) = checkBatter(b).andThen(::mix).andThen(::bake).map { it.uppercase() }

fun main() {
    for (b in listOf(Batter(500), Batter(-1), Batter(5_000))) {
        println("$b:")
        println("  -> ${makeLoaf(b)}")
    }
}
