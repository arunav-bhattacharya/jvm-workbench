package workbench.modernjava.l03.demo

enum class Format { HARDBACK, PAPERBACK, LARGE_PRINT }

sealed interface LoanItem {
    data class Book(val format: Format, val newRelease: Boolean) : LoanItem
    data class Disc(val boxSet: Boolean) : LoanItem
}

// guards in when branches (`is T if condition`) are stable since Kotlin 2.2
fun loanDays(i: LoanItem): Int = when (i) {
    is LoanItem.Book if i.format == Format.LARGE_PRINT -> 42   // 1
    is LoanItem.Book if i.newRelease -> 7                      // 2
    is LoanItem.Book -> 21                                     // 3
    is LoanItem.Disc if i.boxSet -> 14
    is LoanItem.Disc -> 7
}

/** Branches are tried from the top, and the first one that matches wins. Guards decide the order. */
fun main() {
    val items = listOf(
        LoanItem.Book(Format.LARGE_PRINT, false),
        LoanItem.Book(Format.LARGE_PRINT, true),
        LoanItem.Book(Format.HARDBACK, true),
        LoanItem.Book(Format.PAPERBACK, false),
        LoanItem.Disc(true),
    )
    for (i in items) {
        println("%-42s %d days".format(i, loanDays(i)))
    }
}
