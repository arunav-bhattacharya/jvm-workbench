package workbench.modernjava.l03.demo

sealed interface Item {
    data class Book(val title: String, val author: String) : Item
    data class Disc(val title: String, val minutes: Int) : Item
    data class Magazine(val title: String, val issue: Int) : Item
}

// an if-chain: kotlinc never checks that it covers every Item
fun viaChain(i: Item): String =
    if (i is Item.Book) "book ${i.title} by ${i.author}"            // smart cast: i is a Book here
    else if (i is Item.Disc) "disc ${i.title}, ${i.minutes} min"
    else if (i is Item.Magazine) "magazine ${i.title} #${i.issue}"
    else throw IllegalStateException("unreachable?")

// when with a subject: kotlinc checks that every Item is covered
fun viaWhen(i: Item): String = when (i) {
    is Item.Book -> "book ${i.title} by ${i.author}"
    is Item.Disc -> "disc ${i.title}, ${i.minutes} min"
    is Item.Magazine -> "magazine ${i.title} #${i.issue}"
}

// a smart cast lasts for the rest of the function after a negated check returns
fun author(o: Any): String {
    if (o !is Item.Book) return "not a book"
    return "by ${o.author}"
}

/** The same sorting three ways: an if-chain, an early return, and a when. */
fun main() {
    val returns = listOf(Item.Book("Emma", "Jane Austen"), Item.Disc("Paddington", 95), Item.Magazine("Garden Monthly", 214))
    for (i in returns) {
        println(viaChain(i) + "  |  " + viaWhen(i))
    }
    println(author(returns[0]) + ", " + author("Emma"))
}
