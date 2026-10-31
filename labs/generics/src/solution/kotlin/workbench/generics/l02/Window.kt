package workbench.generics.l02

class Window<T : Comparable<T>>(val start: T, val endInclusive: T) {

    init {
        require(start <= endInclusive) { "start $start is after end $endInclusive" }
    }

    operator fun contains(value: T): Boolean = start <= value && value <= endInclusive

    fun clamp(value: T): T = when {
        value < start -> start
        value > endInclusive -> endInclusive
        else -> value
    }

    // two windows miss each other only when one ends before the other starts
    fun overlaps(other: Window<T>): Boolean =
        !(endInclusive < other.start || other.endInclusive < start)
}
