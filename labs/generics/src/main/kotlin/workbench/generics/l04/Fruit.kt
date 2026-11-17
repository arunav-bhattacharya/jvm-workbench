package workbench.generics.l04

/** A piece of fruit. An interface, so Dispenser<Apple> and Dispenser<Lemon> are both candidates for Dispenser<Fruit>. */
interface Fruit {
    val name: String
    val grams: Int
}

data class Apple(override val name: String, override val grams: Int) : Fruit

data class Lemon(override val name: String, override val grams: Int) : Fruit
