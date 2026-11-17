package workbench.generics.l04

/**
 * A tray of items with an optional label card, such as the fruit set out for the window display.
 *
 * TODO 1: make Tray covariant: a Tray<Apple> is a fine Tray<Fruit>. Add `out`.
 * Does `map` still compile after that? Predict first. (Its parameter has type (T) -> R.)
 * TODO 2: write map.
 */
data class Tray<T>(val items: List<T>, val label: String?) {

    /** A tray with [f] applied to every item, and the same label. */
    fun <R> map(f: (T) -> R): Tray<R> = TODO("transform the items, keep the label")
}

/** The first piece of fruit on [tray], or null when the tray is empty. */
fun firstOnTray(tray: Tray<Fruit>): Fruit? = TODO("first item or null")
