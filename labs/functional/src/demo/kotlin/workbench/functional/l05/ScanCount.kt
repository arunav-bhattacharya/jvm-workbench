package workbench.functional.l05

data class Auth(val id: Long, val amountCents: Long)

/** A million authorizations; the first suspicious one (over 20,000.00) is number 518. */
private val feed = List(1_000_000) { i -> Auth(i + 1L, if (i % 1_000 == 517) 2_500_000 else 1_000L + i % 90_000) }

private var scored = 0
private var pulled = 0

/** Stands for a call to the fraud model. Counts every call. */
private fun risk(a: Auth): Int { scored++; return if (a.amountCents > 2_000_000) 95 else 10 }

private fun report(label: String, found: Auth?) {
    println("%-22s scored %,9d  pulled %,9d  found id %s".format(label, scored, pulled, found?.id))
    scored = 0; pulled = 0
}

fun main() {
    report("List chain", feed.map { it to risk(it) }.filter { it.second >= 90 }.map { it.first }.firstOrNull())
    report("Sequence chain", feed.asSequence().map { it to risk(it) }.filter { it.second >= 90 }.map { it.first }.firstOrNull())
    report("Sequence + sortedBy", feed.asSequence().onEach { pulled++ }.sortedBy { it.id }.firstOrNull { risk(it) >= 90 })
    report("firstOrNull { }", feed.firstOrNull { risk(it) >= 90 })
}
