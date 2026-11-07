package workbench.patterns.l06

sealed interface PricingRule {
    data class Flat(val minor: Long) : PricingRule

    data class Percent(val bps: Int) : PricingRule

    data class AllOf(val rules: List<PricingRule>) : PricingRule {
        constructor(vararg rules: PricingRule) : this(rules.toList())
    }

    data class CheapestOf(val rules: List<PricingRule>) : PricingRule {
        init { require(rules.isNotEmpty()) { "CheapestOf needs at least one rule" } }
        constructor(vararg rules: PricingRule) : this(rules.toList())
    }

    data class Capped(val rule: PricingRule, val capMinor: Long) : PricingRule
}

// one when, no else: add a sixth node type and this stops compiling until you price it
fun PricingRule.fee(amountMinor: Long): Long = when (this) {
    is PricingRule.Flat -> minor                                      // leaves compute
    is PricingRule.Percent -> amountMinor * bps / 10_000
    is PricingRule.AllOf -> rules.sumOf { it.fee(amountMinor) }       // groups ask their children
    is PricingRule.CheapestOf -> rules.minOf { it.fee(amountMinor) }
    is PricingRule.Capped -> minOf(rule.fee(amountMinor), capMinor)
}

// a second operation over the same tree: no new classes, just another function
fun PricingRule.describe(): String = when (this) {
    is PricingRule.Flat -> minor.toString()
    is PricingRule.Percent -> "%d.%02d%%".format(bps / 100, bps % 100)
    is PricingRule.AllOf -> rules.joinToString(" + ", "(", ")") { it.describe() }
    is PricingRule.CheapestOf -> rules.joinToString(", ", "cheapest(", ")") { it.describe() }
    is PricingRule.Capped -> "min(${rule.describe()}, $capMinor)"
}
