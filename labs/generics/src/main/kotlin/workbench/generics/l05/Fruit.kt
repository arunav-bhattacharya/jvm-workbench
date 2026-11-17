package workbench.generics.l05

/** The shop's fruit, as in lesson 4. An interface, so a Bin<Fruit> can take apples and lemons alike. */
interface Fruit {
    val name: String
    val grams: Int
}

data class Apple(override val name: String, override val grams: Int) : Fruit

data class Lemon(override val name: String, override val grams: Int) : Fruit
