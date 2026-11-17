package workbench.generics.l10

/** Two kinds of order the shop packs. Both have a variety, a weight and a note; each adds one field. */
data class GiftBox(val grams: Int, val variety: String, val note: String, val ribbon: String)
data class Delivery(val grams: Int, val variety: String, val note: String, val address: String)

/** The shop's fruit, as in the earlier lessons. */
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit
