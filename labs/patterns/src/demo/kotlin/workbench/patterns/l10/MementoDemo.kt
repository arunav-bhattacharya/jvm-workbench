package workbench.patterns.l10

// A shelf that can hand out a photo of itself and later be put back exactly as in the photo.

class Shelf {
    private val items = mutableListOf<String>()
    private var sign = ""

    fun add(item: String) { items += item }
    fun sign(text: String) { sign = text }
    override fun toString() = "$items sign=$sign"

    // callers see an opaque Memento; only Shelf can read the Photo inside it
    interface Memento
    private data class Photo(val items: List<String>, val sign: String) : Memento

    fun save(): Memento = Photo(items.toList(), sign)            // copy: later changes must not leak in

    fun restore(m: Memento) {
        val p = m as Photo
        items.clear()
        items += p.items                                          // copy back in: the photo stays as it was
        sign = p.sign
    }
}

fun main() {
    val shelf = Shelf()
    shelf.add("rye bread")
    val before = shelf.save()
    shelf.add("jam")
    shelf.sign("Autumn sale")
    println("changed:  $shelf")
    shelf.restore(before)
    println("restored: $shelf")
}
