package workbench.generics.l09

/** The shop's fruit, as in the earlier lessons. */
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit
data class Lemon(override val name: String, override val grams: Int) : Fruit

/** Tools the shop looks up by their type. */
interface Scale { fun weigh(fruit: Fruit): String }
interface LabelPrinter { fun labelFor(fruit: Fruit): String }

class ShopScale(private val name: String) : Scale {
    override fun weigh(fruit: Fruit) = "$name: ${fruit.name} weighs ${fruit.grams} g"
}
class PlainLabels : LabelPrinter {
    override fun labelFor(fruit: Fruit) = "${fruit.name}, ${fruit.grams} g"
}

/** A generic tool: Shelf<Apple> and Shelf<Lemon> are different types with ONE class, Shelf. */
interface Shelf<out T> { fun all(): List<T> }
class FixedShelf<out T>(private val items: List<T>) : Shelf<T> {
    override fun all(): List<T> = items
}
