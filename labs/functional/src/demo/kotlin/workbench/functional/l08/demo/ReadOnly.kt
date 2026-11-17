package workbench.functional.l08.demo

import java.math.BigDecimal

data class Menu(val id: String, val dishes: List<String>)
data class Price(val item: String, val amount: BigDecimal)
data class Card(val recipe: String, val notes: MutableList<String>)

fun main() {
    // 1. a read-only List can be a view of a list someone else still changes
    val backing = mutableListOf("soup")
    val menu = Menu("week-7", backing)
    backing += "pie"
    println("1. menu after the caller adds pie: ${menu.dishes}")

    // 2. read-only is a compile-time view: a cast gets around it
    (menu.dishes as MutableList<String>) += "cake"
    println("2. after a cast and an add:      ${menu.dishes}")

    // 3. listOf gives a fixed-size view of an array on the JVM
    val fixed = listOf("soup", "pie")
    println("3. listOf's class: ${fixed.javaClass.name}")
    (fixed as MutableList<String>)[0] = "stew"
    println("   after set(0, \"stew\"): $fixed")
    try {
        fixed.add("cake")
    } catch (e: UnsupportedOperationException) {
        println("   add: UnsupportedOperationException")
    }

    // 4. copy() is shallow: both copies share one list
    val a = Card("pancakes", mutableListOf("use buttermilk"))
    val b = a.copy(recipe = "waffles")
    b.notes += "double the sugar"
    println("4. a.notes = ${a.notes}, same list: ${a.notes === b.notes}")

    // 5. BigDecimal.equals compares the scale too, and data class equals uses it
    println("5. Price(2.50) == Price(2.5): ${Price("butter", BigDecimal("2.50")) == Price("butter", BigDecimal("2.5"))}")
    println("   compareTo says equal: ${BigDecimal("2.50").compareTo(BigDecimal("2.5")) == 0}")
}
