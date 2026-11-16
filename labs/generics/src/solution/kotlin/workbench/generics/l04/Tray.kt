package workbench.generics.l04

// out T: items is a List<T> val (out-position), and map's parameter (T) -> R puts T in the
// parameter of a parameter: two flips, so T is still only coming out.
data class Tray<out T>(val items: List<T>, val label: String?) {

    fun <R> map(f: (T) -> R): Tray<R> = Tray(items.map(f), label)
}

fun firstOnTray(tray: Tray<Fruit>): Fruit? = tray.items.firstOrNull()
