package workbench.patterns.l06

/**
 * A merchant's fee plan as a tree. [Flat] and [Percent] are leaves; [AllOf], [CheapestOf] and
 * [Capped] hold other rules. Every node is a [PricingRule], so code that prices a payment never
 * has to ask "is this a leaf or a group?".
 *
 * Amounts are in minor units (cents). Percentages are basis points: 290 bps = 2.90%.
 * Use integer division, as the card schemes' fee tables do.
 */
sealed interface PricingRule {
    /** A fixed fee, whatever the amount. */
    data class Flat(val minor: Long) : PricingRule

    /** [bps] basis points of the amount. */
    data class Percent(val bps: Int) : PricingRule

    /** The sum of all its rules. An empty AllOf charges 0. */
    data class AllOf(val rules: List<PricingRule>) : PricingRule {
        constructor(vararg rules: PricingRule) : this(rules.toList())
    }

    /** The smallest fee any one of its rules would charge. */
    data class CheapestOf(val rules: List<PricingRule>) : PricingRule {
        init { require(rules.isNotEmpty()) { "CheapestOf needs at least one rule" } }
        constructor(vararg rules: PricingRule) : this(rules.toList())
    }

    /** Whatever [rule] charges, but never more than [capMinor]. */
    data class Capped(val rule: PricingRule, val capMinor: Long) : PricingRule
}

/**
 * The fee this rule charges on [amountMinor]. Write it as ONE `when (this)` with a branch per node
 * type and no `else`, calling `fee` again on the children of group nodes.
 */
fun PricingRule.fee(amountMinor: Long): Long =
    TODO("one when over the five node types: leaves compute, groups ask their children")

/**
 * A one-line description for logs and the merchant dashboard:
 *
 *  - `Flat(30)` is `30`; `Percent(290)` is `2.90%`; `Percent(5)` is `0.05%`
 *  - `AllOf(a, b)` is `(a + b)`, and an empty AllOf is `()`
 *  - `CheapestOf(a, b)` is `cheapest(a, b)`
 *  - `Capped(r, 500)` is `min(r, 500)`
 */
fun PricingRule.describe(): String =
    TODO("one when again; joinToString builds the group forms")
