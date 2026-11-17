package workbench.patterns.l04

import kotlin.math.roundToLong

// A row from a supplier's price list, with the supplier's names and units.
class SupplierItem(val code: String, val qty: String, val unit: String, val avail: String)

// Our own type.
data class Product(val code: String, val grams: Long, val inStock: Boolean)

// An extension function is a light adapter: it reads like a method on the supplier's type,
// lives in our code, and keeps the mapping in one place.
fun SupplierItem.toProduct(): Product {
    val perUnit = when (unit) {
        "KG" -> 1_000.0
        "LB" -> 453.59237                       // the supplier abroad still weighs in pounds
        else -> error("unknown unit $unit")
    }
    return Product(
        code = code,
        grams = (qty.toDouble() * perUnit).roundToLong(),
        inStock = avail == "Y",
    )
}

fun main() {
    val fromSupplier = listOf(
        SupplierItem("T-1001", "2.5", "KG", "Y"),
        SupplierItem("T-1002", "1.5", "LB", "Y"),
        SupplierItem("T-1003", "10", "KG", "N"),
    )
    fromSupplier.map { it.toProduct() }.forEach(::println)
}
