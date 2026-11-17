package workbench.modernjava.l04.demo

// what can happen on a member's account
sealed interface Activity {
    data class Borrowed(val title: String, val days: Int) : Activity
    data class Returned(val title: String) : Activity
    data class Renewed(val title: String, val extraDays: Int) : Activity

    // Step 3: uncomment this class.
    // data class Lost(val title: String, val daysOverdue: Int) : Activity
}

// operation 1: how the activity changes the number of books the member has out
fun booksOutDelta(a: Activity): Int = when (a) {
    is Activity.Borrowed -> 1
    is Activity.Returned -> -1
    is Activity.Renewed -> 0
}

// operation 2: the line in the member's history
fun historyLine(a: Activity): String = when (a) {
    is Activity.Borrowed -> "borrowed ${a.title} for ${a.days} days"
    is Activity.Returned -> "returned ${a.title}"
    is Activity.Renewed -> "renewed  ${a.title} for ${a.extraDays} more days"
}

// Step 2: write operation 3 here, sendsReceipt(Activity), as one more when.

/** Data in data classes, operations in functions. Add an operation, then add a type, and compare the cost. */
fun main() {
    val week = listOf(Activity.Borrowed("Dune", 21), Activity.Borrowed("Emma", 21), Activity.Returned("Dune"), Activity.Renewed("Emma", 14))
    var booksOut = 0
    for (a in week) {
        booksOut += booksOutDelta(a)
        println(historyLine(a))
    }
    println("books out: $booksOut")
}
