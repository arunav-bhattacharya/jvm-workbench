package workbench.coroutines.l07

// Shared model. This file is the same in src/main and src/solution.

data class Item(val name: String, val priceCents: Long)

data class ItemPage(val items: List<Item>, val nextCursor: String?)

/**
 * The grocer's online shop, one page of an aisle at a time. The first page has cursor null;
 * the last page has nextCursor null.
 */
fun interface GroceryShop {
    suspend fun page(aisle: String, cursor: String?): ItemPage
}

/** An old reader for the delivery note file. readLine() BLOCKS, and returns null at the end. */
fun interface LineReader {
    fun readLine(): String?
}

data class DeliveryLine(val item: String, val quantity: Long, val unit: String)

/** Parses "flour,2000,g". */
fun parseLine(line: String): DeliveryLine {
    val (item, quantity, unit) = line.split(",")
    return DeliveryLine(item, quantity.toLong(), unit)
}

sealed interface StockEvent {
    data class Stocked(val item: String) : StockEvent
    data class Aborted(val reason: String) : StockEvent
}
