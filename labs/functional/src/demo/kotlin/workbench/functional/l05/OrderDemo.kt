package workbench.functional.l05

enum class TxnStatus { SETTLED, PENDING, FAILED }

data class Txn(val id: Int, val merchant: String, val amountCents: Long, val status: TxnStatus)

val txns = listOf(
    Txn(1, "acme", 1_500, TxnStatus.SETTLED),
    Txn(2, "globex", 9_900, TxnStatus.PENDING),
    Txn(3, "acme", 2_000, TxnStatus.SETTLED),
    Txn(4, "initech", 12_000, TxnStatus.FAILED),
    Txn(5, "globex", 700, TxnStatus.SETTLED),
)

/** The same three steps on a List and on a Sequence. Predict the print order before you run it. */
fun main() {
    println("List chain:")
    val eager = txns
        .filter { println("  filter ${it.id}"); it.status == TxnStatus.SETTLED }
        .map { println("  map ${it.id}"); it.amountCents }
        .take(2)
    println("  result $eager")

    println("Sequence chain:")
    val lazy = txns.asSequence()
        .filter { println("  filter ${it.id}"); it.status == TxnStatus.SETTLED }
        .map { println("  map ${it.id}"); it.amountCents }
        .take(2)
    println("  built ${lazy::class.simpleName}, nothing has run yet")
    println("  result ${lazy.toList()}")
}
