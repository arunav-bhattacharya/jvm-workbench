package workbench.patterns.l06

// A fee plan as a tree. Leaves and groups share one sealed type, so one `when` prices them all.

sealed interface FeeRule {
    data class Flat(val minor: Long) : FeeRule
    data class Percent(val bps: Int) : FeeRule
    class AllOf(rules: List<FeeRule>) : FeeRule {
        val rules: List<FeeRule> = rules.toList()      // copy what we were given: the tree stays immutable
    }
}

private fun fee(r: FeeRule, amountMinor: Long): Long = when (r) {   // no else: a new node type breaks the build
    is FeeRule.Flat -> r.minor
    is FeeRule.Percent -> amountMinor * r.bps / 10_000
    is FeeRule.AllOf -> r.rules.sumOf { fee(it, amountMinor) }
}

private fun describe(r: FeeRule): String = when (r) {
    is FeeRule.Flat -> r.minor.toString()
    is FeeRule.Percent -> "%d.%02d%%".format(r.bps / 100, r.bps % 100)
    is FeeRule.AllOf -> r.rules.joinToString(" + ", "(", ")") { describe(it) }
}

fun main() {
    val bundle = mutableListOf<FeeRule>(FeeRule.Flat(5))
    val plan = FeeRule.AllOf(listOf(FeeRule.Flat(30), FeeRule.Percent(290), FeeRule.AllOf(bundle)))
    println("plan: ${describe(plan)}")
    println("fee on 100.00: ${fee(plan, 10_000)}")
    println("fee on 1,000.00: ${fee(plan, 100_000)}")

    bundle += FeeRule.Flat(1_000)                       // someone edits the list they passed in
    println("after editing the source list: ${describe(plan)}")
}
