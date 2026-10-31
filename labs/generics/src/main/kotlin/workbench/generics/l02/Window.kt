package workbench.generics.l02

/**
 * A closed window of values from [start] to [endInclusive], both included.
 * Works for any comparable type: amounts, dates, version numbers, strings.
 *
 * Write the bodies. Every comparison goes through the bound `T : Comparable<T>`.
 */
class Window<T : Comparable<T>>(val start: T, val endInclusive: T) {

    init {
        // TODO: throw IllegalArgumentException when start is after endInclusive
    }

    /** True when [value] is inside the window, ends included. Lets you write `x in window`. */
    operator fun contains(value: T): Boolean = TODO("start <= value <= endInclusive")

    /** Returns [value] moved into the window: start if it is below, endInclusive if it is above. */
    fun clamp(value: T): T = TODO("move value inside the window")

    /** True when the two windows share at least one value. */
    fun overlaps(other: Window<T>): Boolean = TODO("neither window ends before the other starts")
}
