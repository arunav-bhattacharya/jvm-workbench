package workbench.generics.l11

/** The shop's fruit. Each delivery is one piece of fruit, and it rings the bell for its kind. */
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit
data class Lemon(override val name: String, override val grams: Int) : Fruit

/** Things the storeroom keeps, with ids of different types. */
data class Supplier(override val id: Long, val name: String) : Item<Long>
data class Crate(override val id: String, val grams: Int) : Item<String>
