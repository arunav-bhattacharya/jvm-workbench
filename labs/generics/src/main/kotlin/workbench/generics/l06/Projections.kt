package workbench.generics.l06

/**
 * MutableList is invariant: it reads AND writes T, so it can't be declared out or in.
 * These functions only read from one list or only write to another, so each can ask for a
 * PROJECTION of MutableList: `MutableList<out T>` (read-only view) or `MutableList<in T>` (write-only view).
 *
 * TODO for each function below: add the projection that matches what the function does with the list.
 * The tests check the Java signatures: Kotlin compiles `MutableList<out T>` to `List<? extends T>`
 * and `MutableList<in T>` to `List<? super T>`.
 */

/**
 * Appends every item of [from] to [to], in order, and returns how many were copied.
 * [from] is only read. [to] is only written. Afterwards a MutableList<Int> should be copyable
 * into a MutableList<Number>.
 */
fun <T> copyInto(from: MutableList<T>, to: MutableList<T>): Int =
    TODO("add out/in projections to the parameters, then copy")

/** Appends [count] copies of [value] to [target]. [target] is only written to. */
fun <T> fillWith(target: MutableList<T>, value: T, count: Int) {
    TODO("add a projection to target, then append")
}

/**
 * The sum of all amounts, as a Double. The tests pass a List<Int> and a List<Double>.
 * This one needs NO projection: List is declared `List<out E>` already. Try writing
 * `List<out Number>` anyway, and read the warning the compiler gives you.
 */
fun sumAll(amounts: List<Number>): Double =
    TODO("add up amounts with toDouble()")
