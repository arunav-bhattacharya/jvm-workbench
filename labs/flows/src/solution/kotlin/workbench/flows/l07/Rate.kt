package workbench.flows.l07

import java.math.BigDecimal

/** One FX mid rate, for example EURUSD at 1.0852. Equality is the data class's: pair and mid. */
data class Rate(val pair: String, val mid: BigDecimal)
