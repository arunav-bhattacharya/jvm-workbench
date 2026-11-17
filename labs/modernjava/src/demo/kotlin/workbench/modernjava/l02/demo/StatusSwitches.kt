package workbench.modernjava.l02.demo

// where one copy of a book is right now
sealed interface CopyStatus {
    data class OnShelf(val shelfmark: String) : CopyStatus
    data class OnLoan(val memberId: String, val daysLeft: Int) : CopyStatus
    data class OnHold(val memberId: String) : CopyStatus
    data class Missing(val daysMissing: Int) : CopyStatus

    // Step 2: uncomment this class. Kotlin has no permits clause to edit.
    // data class InRepair(val daysLeft: Int) : CopyStatus
}

fun label(s: CopyStatus): String = when (s) {                // exhaustive, no else
    is CopyStatus.OnShelf -> "on shelf"
    is CopyStatus.OnLoan -> "on loan"
    is CopyStatus.OnHold -> "on hold"
    is CopyStatus.Missing -> "missing"
}

fun canLendToday(s: CopyStatus): Boolean = when (s) {        // exhaustive, no else
    is CopyStatus.OnShelf -> true
    is CopyStatus.OnLoan -> false
    is CopyStatus.OnHold -> false
    is CopyStatus.Missing -> false
}

fun reminderDays(s: CopyStatus): Int = when (s) {
    is CopyStatus.OnLoan -> s.daysLeft                       // remind the member before it's due
    is CopyStatus.OnHold -> 3                                // the member has three days to collect it
    else -> 0                                                // "and anything else": the compiler stops checking
}

/** Three whens over one sealed type. Add a subtype and see which ones the compiler finds. */
fun main() {
    val copies = listOf(CopyStatus.OnShelf("FIC 12"), CopyStatus.OnLoan("M-1042", 9), CopyStatus.OnHold("M-2210"), CopyStatus.Missing(40))
    for (s in copies) {
        println("%-9s lend today: %-5s  reminder in %d days".format(label(s), canLendToday(s), reminderDays(s)))
    }
}
