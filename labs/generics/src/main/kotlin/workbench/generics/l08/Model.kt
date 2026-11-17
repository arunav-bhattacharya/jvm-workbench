package workbench.generics.l08

import java.math.BigDecimal

/** The shop's fruit, as in the earlier lessons. */
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit
data class Lemon(override val name: String, override val grams: Int) : Fruit

/** A weight in grams. `Weight.parse("1.25 kg")` is `Weight(1250)`, and `Weight.parse("180 g")` is `Weight(180)`. */
data class Weight(val grams: Int) {
    companion object {
        @JvmStatic
        fun parse(text: String): Weight {
            val (amount, unit) = text.trim().split(" ")
            val grams = when (unit) {
                "kg" -> BigDecimal(amount).movePointRight(3)
                "g" -> BigDecimal(amount)
                else -> throw IllegalArgumentException("unknown unit: $unit")
            }
            return Weight(grams.intValueExact())
        }
    }
}
