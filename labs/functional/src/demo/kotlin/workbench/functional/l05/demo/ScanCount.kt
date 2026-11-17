package workbench.functional.l05.demo

data class RecipeCard(val id: Long, val minutes: Int)

/** A book of a million recipes. The first good match for tonight is number 518. */
private val book = List(1_000_000) { i -> RecipeCard(i + 1L, if (i % 1_000 == 517) 7 else 20 + i % 100) }

private var scored = 0
private var pulled = 0

/** Stands for a call to the matching service: about 2 ms each in the app. Counts every call. */
private fun match(r: RecipeCard): Int { scored++; return if (r.minutes < 10) 95 else 10 }

private fun report(label: String, found: RecipeCard?) {
    println("%-22s scored %,9d  pulled %,9d  found id %s".format(label, scored, pulled, found?.id))
    scored = 0; pulled = 0
}

fun main() {
    report("List chain", book.map { it to match(it) }.filter { it.second >= 90 }.map { it.first }.firstOrNull())
    report("Sequence chain", book.asSequence().map { it to match(it) }.filter { it.second >= 90 }.map { it.first }.firstOrNull())
    report("Sequence + sortedBy", book.asSequence().onEach { pulled++ }.sortedBy { it.id }.firstOrNull { match(it) >= 90 })
    report("firstOrNull { }", book.firstOrNull { match(it) >= 90 })
}
