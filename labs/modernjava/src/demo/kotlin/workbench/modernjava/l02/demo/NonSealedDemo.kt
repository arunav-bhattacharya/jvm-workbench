package workbench.modernjava.l02.demo

// Kotlin subtypes are final unless you open them, and there is no non-sealed keyword:
// a plain interface (or an open class) under a sealed parent is the open branch.
sealed interface LibraryItem {
    data class Book(val title: String) : LibraryItem                         // final: a leaf

    sealed interface Disc : LibraryItem                                       // sealed: closed below
    data class Dvd(val title: String) : Disc
    data class AudioCd(val title: String) : Disc

    interface PartnerItem : LibraryItem {                                     // open below
        val partnerId: String
    }
}

// a partner library's code, which could live in any package: PartnerItem is an ordinary interface
data class ArchiveBox(override val partnerId: String, val contents: String) : LibraryItem.PartnerItem

// A Kotlin sealed class is always abstract, so the trap in step 3 of the Java demo can't happen here.
sealed class Extension {
    class FixedDays(val days: Int) : Extension()
    object SameAgain : Extension()
}

fun describe(item: LibraryItem): String = when (item) {
    is LibraryItem.Book -> "book ${item.title}"
    is LibraryItem.Disc -> "disc $item"                                       // one branch for the sealed branch
    is LibraryItem.PartnerItem -> "partner ${item.partnerId}"                 // one branch for the open branch
}

// how many days a renewal adds to a loan
fun extraDays(e: Extension, loanDays: Int): Int = when (e) {
    is Extension.FixedDays -> e.days
    Extension.SameAgain -> loanDays
}

/** Each branch of a sealed hierarchy ends closed, sealed again, or open. */
fun main() {
    println(describe(LibraryItem.Book("Dune")))
    println(describe(LibraryItem.Dvd("Paddington")))
    println(describe(ArchiveBox("city-archive", "old maps")))
    println("PartnerItem.isSealed(): ${LibraryItem.PartnerItem::class.java.isSealed}")
    println("renewal: ${extraDays(Extension.FixedDays(7), 21)} and ${extraDays(Extension.SameAgain, 21)} extra days")
}
